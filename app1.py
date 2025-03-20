if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        check_if_this_doctor_is_link_to_The_patient=db.doctor_Add_patient(doctor_id,patient_id)
        flash("Patient ajouté avec succès")
    else:
        flash("Le patient donné n'est pas dans la base de données")