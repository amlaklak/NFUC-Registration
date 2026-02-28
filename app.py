from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from flask_mysqldb import MySQL
import MySQLdb.cursors
import csv
from datetime import datetime
import io
import os

app = Flask(__name__)
CORS(app)

# MySQL Configuration (read from environment variables for deployment)
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'nfuc_registration')

mysql = MySQL(app)

# Create database and table if they don't exist
def init_db():
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS nfuc_registration")
        
        # Select database
        cursor.execute("USE nfuc_registration")
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                date_of_birth DATE,
                gender VARCHAR(50),
                nationality VARCHAR(100),
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                province VARCHAR(100),
                district VARCHAR(100),
                village VARCHAR(100),
                program VARCHAR(255),
                school VARCHAR(255),
                qualification VARCHAR(100),
                guardian_name VARCHAR(255),
                guardian_contact VARCHAR(20),
                emergency_contact VARCHAR(20),
                medical_conditions LONGTEXT,
                declaration LONGTEXT,
                application_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        mysql.connection.commit()
        cursor.close()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization error: {e}")

# Initialize database on startup
with app.app_context():
    init_db()

@app.route('/api/register', methods=['POST'])
def register():
    """Handle student registration form submission"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['full_name', 'email', 'phone', 'gender', 'program', 'declaration']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute("""
            INSERT INTO students 
            (full_name, date_of_birth, gender, nationality, email, phone, 
             province, district, village, program, school, qualification, 
             guardian_name, guardian_contact, emergency_contact, medical_conditions, declaration, application_date)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('full_name'),
            data.get('date_of_birth') or None,
            data.get('gender'),
            data.get('nationality'),
            data.get('email'),
            data.get('phone'),
            data.get('province'),
            data.get('district'),
            data.get('village'),
            data.get('program'),
            data.get('school'),
            data.get('qualification'),
            data.get('guardian_name'),
            data.get('guardian_contact'),
            data.get('emergency_contact'),
            data.get('medical_conditions'),
            data.get('declaration'),
            data.get('application_date') or datetime.now().date()
        ))
        
        mysql.connection.commit()
        student_id = cursor.lastrowid
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful!',
            'student_id': student_id
        }), 201
        
    except MySQLdb.IntegrityError as e:
        return jsonify({'error': 'Email already registered'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    """Retrieve all student registrations (admin only)"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
        students = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'success': True,
            'total': len(students),
            'students': students
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Retrieve a specific student registration"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        cursor.close()
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify({
            'success': True,
            'student': student
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Update a student registration"""
    try:
        data = request.json
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if student exists
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        if not cursor.fetchone():
            cursor.close()
            return jsonify({'error': 'Student not found'}), 404
        
        # Update student
        cursor.execute("""
            UPDATE students SET 
            full_name = %s, date_of_birth = %s, gender = %s, nationality = %s, 
            email = %s, phone = %s, province = %s, district = %s, village = %s, 
            program = %s, school = %s, qualification = %s, guardian_name = %s, 
            guardian_contact = %s, emergency_contact = %s, medical_conditions = %s, 
            declaration = %s WHERE id = %s
        """, (
            data.get('full_name'),
            data.get('date_of_birth'),
            data.get('gender'),
            data.get('nationality'),
            data.get('email'),
            data.get('phone'),
            data.get('province'),
            data.get('district'),
            data.get('village'),
            data.get('program'),
            data.get('school'),
            data.get('qualification'),
            data.get('guardian_name'),
            data.get('guardian_contact'),
            data.get('emergency_contact'),
            data.get('medical_conditions'),
            data.get('declaration'),
            student_id
        ))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Student updated successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student registration"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        mysql.connection.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            return jsonify({'error': 'Student not found'}), 404
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Student deleted successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    """Export all student registrations as CSV"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
        students = cursor.fetchall()
        cursor.close()
        
        if not students:
            return jsonify({'error': 'No students to export'}), 404
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=students[0].keys())
        writer.writeheader()
        writer.writerows(students)
        
        # Convert to bytes
        output.seek(0)
        bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        
        return send_file(
            bytes_output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'nfuc_registrations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get registration statistics"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Total registrations
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total = cursor.fetchone()['total']
        
        # By gender
        cursor.execute("SELECT gender, COUNT(*) as count FROM students GROUP BY gender")
        by_gender = cursor.fetchall()
        
        # By program
        cursor.execute("SELECT program, COUNT(*) as count FROM students GROUP BY program ORDER BY count DESC LIMIT 10")
        by_program = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'success': True,
            'total_registrations': total,
            'by_gender': by_gender,
            'by_program': by_program
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    """Admin dashboard to view registrations"""
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
        students = cursor.fetchall()
        cursor.close()
        
        return render_template('admin.html', students=students)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/', methods=['GET'])
def index():
    """Serve the registration form"""
    return send_file('static/nfuc_registration_form.html')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Read PORT from environment (platforms like Render/Heroku set this)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=port, debug=debug)
