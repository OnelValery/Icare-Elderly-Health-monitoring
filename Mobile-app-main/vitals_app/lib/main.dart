import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() => runApp(MaterialApp(
  debugShowCheckedModeBanner: false,
  home: AuthWrapper(),
));

class Patient {
  final String id;
  final String name;

  Patient({required this.id, required this.name});
}

class AuthWrapper extends StatefulWidget {
  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  Patient? patient;

  @override
  Widget build(BuildContext context) {
    return patient == null
        ? LoginScreen(onLoginSuccess: (p) => setState(() => patient = p))
        : VitalsHomePage(
            patient: patient!,
            onLogout: () => setState(() => patient = null),
          );
  }
}

class LoginScreen extends StatefulWidget {
  final Function(Patient) onLoginSuccess;
  const LoginScreen({required this.onLoginSuccess});

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  String error = '';

  Future<void> login() async {
    final response = await http.post(
      Uri.parse('http://192.168.43.76:5001/api/login'),
      headers: {"Content-Type": "application/json"},
      body: json.encode({
        'email': emailController.text,
        'password': passwordController.text,
      }),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final patient = Patient(
        id: data['patient_id'],
        name: '${data['first_name']} ${data['last_name']}',
      );
      widget.onLoginSuccess(patient);
    } else {
      setState(() {
        error = 'Login failed. Check credentials.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Patient Login')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              SizedBox(height: 30),
              Image.asset('assets/images/icare_logo.png', height: 120),
              SizedBox(height: 16),
              Text(
                'Patient Login',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 24),
              TextField(
                controller: emailController,
                decoration: InputDecoration(labelText: 'Email'),
              ),
              TextField(
                controller: passwordController,
                decoration: InputDecoration(labelText: 'Password'),
                obscureText: true,
              ),
              SizedBox(height: 16),
              ElevatedButton(
                onPressed: login,
                child: Text('Login'),
              ),
              if (error.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 10),
                  child: Text(error, style: TextStyle(color: Colors.red)),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class VitalsHomePage extends StatefulWidget {
  final Patient patient;
  final VoidCallback onLogout;

  const VitalsHomePage({required this.patient, required this.onLogout});

  @override
  _VitalsHomePageState createState() => _VitalsHomePageState();
}

class _VitalsHomePageState extends State<VitalsHomePage> {
  int bpm = 0;
  int spo2 = 0;
  double temperature = 0.0;
  int steps = 0;
  bool fallDetected = false;
  bool loading = false;
  Timer? refreshTimer;

  Future<void> fetchVitals() async {
    try {
      final response = await http.get(
        Uri.parse('http://192.168.43.76:5001/data/${widget.patient.id}'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        if (!mounted) return;

        final newBpm = data['bpm'];
        final newSpo2 = data['spo2'];
        final newTemp = data['temperature'];
        final newSteps = data['stepCount'];
        final newFall = data['fall'];

        // Only update UI if values changed
        if (newBpm != bpm ||
            newSpo2 != spo2 ||
            newTemp != temperature ||
            newSteps != steps ||
            newFall != fallDetected) {
          setState(() {
            bpm = newBpm;
            spo2 = newSpo2;
            temperature = newTemp;
            steps = newSteps;
            fallDetected = newFall;
          });
        }
      }
    } catch (e) {
      print("Error fetching vitals: $e");
    }
  }

  @override
  void initState() {
    super.initState();
    fetchVitals();
    refreshTimer = Timer.periodic(Duration(seconds: 2), (_) => fetchVitals());
  }

  @override
  void dispose() {
    refreshTimer?.cancel();
    super.dispose();
  }

  Widget buildVitalCard({
    required IconData icon,
    required String label,
    required String value,
    Color? backgroundColor,
  }) {
    return Card(
      color: backgroundColor,
      elevation: 2,
      margin: EdgeInsets.symmetric(vertical: 6),
      child: ListTile(
        leading: Icon(icon, color: Colors.teal),
        title: Text(label),
        trailing: Text(
          value,
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('ESP32 Vitals Monitor'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: widget.onLogout,
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            const Image(image: AssetImage('assets/images/icare_logo.png'), height: 100),
            SizedBox(height: 10),
            Text(
              'iCare Health Monitor',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.teal[700],
              ),
            ),
            SizedBox(height: 6),
            Text(
              '${widget.patient.name} (${widget.patient.id})',
              style: TextStyle(fontSize: 16, color: Colors.grey[700]),
            ),
            SizedBox(height: 20),
            buildVitalCard(
              icon: Icons.favorite,
              label: "Heart Rate",
              value: bpm == 0 ? "Waiting..." : "$bpm bpm",
            ),
            buildVitalCard(
              icon: Icons.bloodtype,
              label: "SpO₂",
              value: spo2 == 0 ? "Waiting..." : "$spo2%",
            ),
            // buildVitalCard(
            //   icon: Icons.thermostat,
            //   label: "Temperature",
            //   value: "${temperature.toStringAsFixed(1)} °C",
            // ),
            buildVitalCard(
              icon: Icons.directions_walk,
              label: "Steps",
              value: "$steps",
            ),
            buildVitalCard(
              icon: fallDetected ? Icons.warning : Icons.check_circle,
              label: "Fall Detected",
              value: fallDetected ? "YES" : "No",
              backgroundColor: fallDetected ? Colors.red[100] : null,
            ),
            SizedBox(height: 20),
            ElevatedButton.icon(
              icon: Icon(Icons.refresh),
              label: Text("Refresh"),
              onPressed: fetchVitals,
            ),
          ],
        ),
      ),
    );
  }
}