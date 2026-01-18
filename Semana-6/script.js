document.addEventListener('DOMContentLoaded', function() {
    // Obtener referencias a los elementos del formulario
    const form = document.getElementById('registrationForm');
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const ageInput = document.getElementById('age');
    const submitBtn = document.getElementById('submitBtn');
    const resetBtn = document.getElementById('resetBtn');
    
    // Obtener referencias a los elementos de error
    const nameError = document.getElementById('nameError');
    const emailError = document.getElementById('emailError');
    const passwordError = document.getElementById('passwordError');
    const confirmPasswordError = document.getElementById('confirmPasswordError');
    const ageError = document.getElementById('ageError');
    
    // Obtener referencias a los elementos de estado de validación
    const nameStatus = document.getElementById('nameStatus');
    const emailStatus = document.getElementById('emailStatus');
    const passwordStatus = document.getElementById('passwordStatus');
    const confirmPasswordStatus = document.getElementById('confirmPasswordStatus');
    const ageStatus = document.getElementById('ageStatus');
    const formStatus = document.getElementById('formStatus');
    
    // Expresión regular para validar email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    // Expresión regular para validar contraseña (mínimo 8 caracteres, al menos un número y un carácter especial)
    const passwordRegex = /^(?=.*[0-9])(?=.*[!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{8,}$/;
    
    // Objeto para almacenar el estado de validación de cada campo
    const validationState = {
        name: false,
        email: false,
        password: false,
        confirmPassword: false,
        age: false
    };
    
    // Función para actualizar el estado del botón de envío
    function updateSubmitButton() {
        const allValid = Object.values(validationState).every(value => value === true);
        
        if (allValid) {
            submitBtn.disabled = false;
            formStatus.innerHTML = '<i class="fas fa-check-circle valid"></i> Formulario completo y válido';
            formStatus.style.color = '#2ecc71';
        } else {
            submitBtn.disabled = true;
            formStatus.innerHTML = '<i class="fas fa-times-circle"></i> Formulario incompleto';
            formStatus.style.color = '#e74c3c';
        }
    }
    
    // Función para actualizar la apariencia de un campo de entrada
    function updateFieldAppearance(inputElement, isValid) {
        if (isValid) {
            inputElement.classList.remove('invalid');
            inputElement.classList.add('valid');
        } else {
            inputElement.classList.remove('valid');
            inputElement.classList.add('invalid');
        }
    }
    
    // Función para actualizar el estado de validación en el resumen
    function updateValidationStatus(field, isValid) {
        const statusElement = document.getElementById(`${field}Status`);
        if (isValid) {
            statusElement.innerHTML = `<i class="fas fa-check-circle valid"></i> ${getFieldLabel(field)}: Válido`;
            statusElement.style.color = '#2ecc71';
        } else {
            statusElement.innerHTML = `<i class="fas fa-times-circle invalid"></i> ${getFieldLabel(field)}: No válido`;
            statusElement.style.color = '#e74c3c';
        }
    }
    
    // Función auxiliar para obtener la etiqueta del campo
    function getFieldLabel(field) {
        const labels = {
            name: 'Nombre',
            email: 'Correo',
            password: 'Contraseña',
            confirmPassword: 'Confirmación',
            age: 'Edad'
        };
        return labels[field] || field;
    }
    
    // Validación del nombre
    function validateName() {
        const name = nameInput.value.trim();
        const isValid = name.length >= 3;
        
        if (isValid) {
            nameError.textContent = '';
        } else {
            nameError.textContent = name.length === 0 
                ? 'El nombre es obligatorio' 
                : 'El nombre debe tener al menos 3 caracteres';
        }
        
        updateFieldAppearance(nameInput, isValid);
        updateValidationStatus('name', isValid);
        validationState.name = isValid;
        updateSubmitButton();
        
        return isValid;
    }
    
    // Validación del correo electrónico
    function validateEmail() {
        const email = emailInput.value.trim();
        const isValid = emailRegex.test(email);
        
        if (isValid) {
            emailError.textContent = '';
        } else {
            emailError.textContent = email.length === 0 
                ? 'El correo electrónico es obligatorio' 
                : 'Formato de correo electrónico inválido';
        }
        
        updateFieldAppearance(emailInput, isValid);
        updateValidationStatus('email', isValid);
        validationState.email = isValid;
        updateSubmitButton();
        
        return isValid;
    }
    
    // Validación de la contraseña
    function validatePassword() {
        const password = passwordInput.value;
        const isValid = passwordRegex.test(password);
        
        if (isValid) {
            passwordError.textContent = '';
        } else {
            if (password.length === 0) {
                passwordError.textContent = 'La contraseña es obligatoria';
            } else if (password.length < 8) {
                passwordError.textContent = 'La contraseña debe tener al menos 8 caracteres';
            } else if (!/(?=.*[0-9])/.test(password)) {
                passwordError.textContent = 'La contraseña debe contener al menos un número';
            } else if (!/(?=.*[!@#$%^&*])/.test(password)) {
                passwordError.textContent = 'La contraseña debe contener al menos un carácter especial (!@#$%^&*)';
            }
        }
        
        updateFieldAppearance(passwordInput, isValid);
        updateValidationStatus('password', isValid);
        validationState.password = isValid;
        
        // Si la contraseña cambia, también validar la confirmación
        if (confirmPasswordInput.value.length > 0) {
            validateConfirmPassword();
        }
        
        updateSubmitButton();
        return isValid;
    }
    
    // Validación de confirmación de contraseña
    function validateConfirmPassword() {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        const isValid = password === confirmPassword && password.length > 0;
        
        if (isValid) {
            confirmPasswordError.textContent = '';
        } else {
            if (confirmPassword.length === 0) {
                confirmPasswordError.textContent = 'La confirmación de contraseña es obligatoria';
            } else {
                confirmPasswordError.textContent = 'Las contraseñas no coinciden';
            }
        }
        
        updateFieldAppearance(confirmPasswordInput, isValid);
        updateValidationStatus('confirmPassword', isValid);
        validationState.confirmPassword = isValid;
        updateSubmitButton();
        
        return isValid;
    }
    
    // Validación de la edad
    function validateAge() {
        const age = parseInt(ageInput.value);
        const isValid = !isNaN(age) && age >= 18;
        
        if (isValid) {
            ageError.textContent = '';
        } else {
            if (ageInput.value.length === 0) {
                ageError.textContent = 'La edad es obligatoria';
            } else if (isNaN(age)) {
                ageError.textContent = 'La edad debe ser un número válido';
            } else {
                ageError.textContent = 'Debe ser mayor o igual a 18 años';
            }
        }
        
        updateFieldAppearance(ageInput, isValid);
        updateValidationStatus('age', isValid);
        validationState.age = isValid;
        updateSubmitButton();
        
        return isValid;
    }
    
    // Agregar event listeners para validación en tiempo real
    nameInput.addEventListener('input', validateName);
    nameInput.addEventListener('blur', validateName);
    
    emailInput.addEventListener('input', validateEmail);
    emailInput.addEventListener('blur', validateEmail);
    
    passwordInput.addEventListener('input', validatePassword);
    passwordInput.addEventListener('blur', validatePassword);
    
    confirmPasswordInput.addEventListener('input', validateConfirmPassword);
    confirmPasswordInput.addEventListener('blur', validateConfirmPassword);
    
    ageInput.addEventListener('input', validateAge);
    ageInput.addEventListener('blur', validateAge);
    
    // Manejar el envío del formulario
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Validar todos los campos antes de enviar
        const isNameValid = validateName();
        const isEmailValid = validateEmail();
        const isPasswordValid = validatePassword();
        const isConfirmPasswordValid = validateConfirmPassword();
        const isAgeValid = validateAge();
        
        // Si todos los campos son válidos, mostrar alerta de éxito
        if (isNameValid && isEmailValid && isPasswordValid && isConfirmPasswordValid && isAgeValid) {
            alert('¡Formulario enviado con éxito!\n\nValidación completada:\n✓ Nombre válido\n✓ Correo válido\n✓ Contraseña segura\n✓ Confirmación correcta\n✓ Edad permitida\n\nLos datos han sido procesados correctamente.');
            
            // Aquí normalmente se enviarían los datos al servidor
            // form.submit();
        }
    });
    
    // Manejar el reinicio del formulario
    resetBtn.addEventListener('click', function() {
        // Restablecer el estado de validación
        for (let field in validationState) {
            validationState[field] = false;
        }
        
        // Restablecer las clases de los campos de entrada
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            input.classList.remove('valid', 'invalid');
        });
        
        // Limpiar mensajes de error
        const errorMessages = form.querySelectorAll('.error-message');
        errorMessages.forEach(error => {
            error.textContent = '';
        });
        
        // Restablecer estados de validación en el resumen
        const statusElements = [
            nameStatus, emailStatus, passwordStatus, confirmPasswordStatus, ageStatus
        ];
        
        statusElements.forEach(element => {
            element.innerHTML = `<i class="fas fa-times-circle invalid"></i> ${getFieldLabel(element.id.replace('Status', ''))}: No válido`;
            element.style.color = '#e74c3c';
        });
        
        // Actualizar estado del formulario
        formStatus.innerHTML = '<i class="fas fa-times-circle"></i> Formulario incompleto';
        formStatus.style.color = '#e74c3c';
        
        // Deshabilitar el botón de envío
        submitBtn.disabled = true;
        
        // Mostrar mensaje de confirmación
        setTimeout(() => {
            alert('Formulario reiniciado. Todos los campos han sido limpiados.');
        }, 100);
    });
    
    // Inicializar las validaciones al cargar la página
    validateName();
    validateEmail();
    validatePassword();
    validateConfirmPassword();
    validateAge();
});