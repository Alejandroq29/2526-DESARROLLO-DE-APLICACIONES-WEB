
document.addEventListener('DOMContentLoaded', function() {

  
    const botonAlerta = document.getElementById('btnAlerta');
    
    botonAlerta.addEventListener('click', function() {
        alert('¡Hola! Has interactuado con JavaScript correctamente. 🚀');
    });


    
    const formulario = document.getElementById('formularioContacto');
    const errorDiv = document.getElementById('errorMsg');

    formulario.addEventListener('submit', function(evento) {
        
        evento.preventDefault();
        
       
        const nombre = document.getElementById('nombre').value.trim();
        const email = document.getElementById('email').value.trim();
        const mensaje = document.getElementById('mensaje').value.trim();
        
        let mensajesError = [];

        
        if (nombre === '') {
            mensajesError.push('El campo Nombre es obligatorio.');
        }

        if (email === '') {
            mensajesError.push('El campo Correo es obligatorio.');
        } else if (!email.includes('@')) {
             
            mensajesError.push('Por favor ingresa un correo válido.');
        }

        if (mensaje === '') {
            mensajesError.push('El campo Mensaje no puede estar vacío.');
        }

       
        if (mensajesError.length > 0) {
           
            errorDiv.innerHTML = mensajesError.join('<br>');
            errorDiv.classList.remove('d-none'); 
        } else {
          
            errorDiv.classList.add('d-none'); 
            alert('¡Formulario enviado con éxito! Gracias, ' + nombre);
            formulario.reset(); 
        }
    });

});