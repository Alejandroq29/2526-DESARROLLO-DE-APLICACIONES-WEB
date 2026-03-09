#!/usr/bin/env python
# Debug script - step by step imports
print("Python version:", __import__('sys').version)

try:
    print("Importing flask_wtf...")
    from flask_wtf import FlaskForm
    print("✓ FlaskForm imported")
except Exception as e:
    print("✗ Error importing FlaskForm:", e)
    
try:
    print("Importing wtforms...")
    from wtforms import StringField, IntegerField, FloatField, SubmitField
    print("✓ WTForms fields imported")
except Exception as e:
    print("✗ Error importing WTForms:", e)

try:
    print("Importing wtforms.validators...")
    from wtforms.validators import DataRequired
    print("✓ WTForms validators imported")
except Exception as e:
    print("✗ Error importing validators:", e)

# Now try to define the class
try:
    print("Defining ProductoForm...")
    class ProductoForm(FlaskForm):
        nombre = StringField("Nombre", validators=[DataRequired()])
        cantidad = IntegerField("Cantidad", validators=[DataRequired()])
        precio = FloatField("Precio", validators=[DataRequired()])
        submit = SubmitField("Guardar")
    print("✓ ProductoForm defined successfully")
except Exception as e:
    print("✗ Error defining ProductoForm:", e)
    import traceback
    traceback.print_exc()
