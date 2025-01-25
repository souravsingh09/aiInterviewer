# We are building an AI Interviewer Application built with Flask and Python
# This file will be the entry point for the application
# We will have two web pages: 
#   the  first web page is for the Internal team to setup the interview by uploading the Resume, job description, email id to send the results to and the photograph of the interview. On submitting these a url will generated from a randomly generated number
#   On the second page the interview will take place, where first whether the webcam is on or not will be checked. Only if the webcam is on will the start interview button be enabled. 
#   Once the start interview button is clicked, the interview will start with the azure speech service welcoming the candidate and asking the first question.
#   On Conclusion of the interview the transcript of the interview and AI evaluated results will be sent to the email id provided by the internal team.


# IMPORTS
import os
import threading
from Utils_Scheduler_modified import Utils_Scheduler
from flask import Flask, render_template, request, jsonify, redirect, url_for
from Utils_interviewer import Utils_Interviewer



# FLASK APP
app = Flask(__name__)

# ROUTES

# Route for home page should redirect to /schedule interview
@app.route('/')
def home():
    return redirect(url_for('schedule_interview'))
# Route for the first web page where the internal team will setup the interview
@app.route('/schedule_interview', methods=['GET', 'POST']) 
def schedule_interview():
    if request.method == 'POST':
        # Get the form data

        # Creating a Utils object
        global util_scheduler
        util_scheduler = Utils_Scheduler()

        resume = request.files['resume']
        job_description = request.files['job_description']
        # email_id = request.form['email']
        photograph = request.files['photo']

        global unique_id
        unique_id = util_scheduler.generate_key()

        os.makedirs(os.path.join('static/scheduled_interviews', f'{unique_id}'), exist_ok=True)


        # Save the files
        resume_path = os.path.join(os.getcwd(),"static","scheduled_interviews", f'{unique_id}', f'Resume_{unique_id}.{resume.filename.split(".")[-1]}')
        job_description_path = os.path.join(os.getcwd(),"static","scheduled_interviews", f'{unique_id}', f'jd_{unique_id}.{job_description.filename.split(".")[-1]}')
        photograph_path = os.path.join(os.getcwd(),"static","scheduled_interviews", f'{unique_id}', f'photo_{unique_id}.{photograph.filename.split(".")[-1]}')
        resume.save(resume_path)
        job_description.save(job_description_path)
        photograph.save(photograph_path)

        # Run utils.create_json() to create a json file with the details of the interview in a background thread
        thread = threading.Thread(target=util_scheduler.create_json, args=(unique_id, resume_path, job_description_path, photograph_path))

        # Start the thread
        thread.start()
        thread.join()

        global data
        data = util_scheduler.read_json(unique_id)
                
        global url
        url = f"http://127.0.0.1:5000/interview/{unique_id}"

        # Return the url
        return redirect(url_for("screen"))
    return render_template('index.html')

# Route for the second web page where the interview details will be displayed
@app.route('/screen', methods=['GET', 'POST'])
def screen():
    temp_path =  "http://127.0.0.1:5000/" + "/".join(data["photo_path"].split("\\")[3:])
    return render_template('job-single.html', job_role=data["job_role"], vital_topics = ", ".join(data["vital_topics"]), good_to_know_topics=", ".join(data["good_to_know_topics"]),
                           candidate_name = data["candidate_name"], work_experience=data["work_experience"], projects=data["project_titles"], skills=data["technical_skills"],
                           photo_path = temp_path)

# Route for sending the email to the candidate about the interview
@app.route('/send_email', methods=['POST'])
def send_email():
    # Send the email to the candidate
    util_scheduler.email_intimation("jobinmathewsp@outlook.com", unique_id, url)
    return jsonify({"message": "Email sent to the candidate"})
    

# Route for the second web page where the interview will take place
@app.route('/interview/<unique_id>', methods=['GET', 'POST'])
def interview(unique_id):
    list_interviews_created = os.listdir('static/scheduled_interviews')
    # Check if the unique_id is valid
    if unique_id in list_interviews_created:
        # read the json file corresponding to the unique_id into a dictionary
        global utils_interviwer
        utils_interviwer = Utils_Interviewer()
        global interviewer_data
        interviewer_data = utils_interviwer.read_json(unique_id)
        candidate_name = interviewer_data['candidate_name']
        job_role = interviewer_data['job_role']
        photo_filename = os.path.basename(interviewer_data['photo_path'])
    
        return render_template('interview_3.html', candidate_name=candidate_name, job_role=job_role, unique_id=unique_id, photo_filename=photo_filename)
    else:
        return "Invalid URL"
    
# Route for sending the system message to the javascript
@app.route('/system_prompt', methods=['POST'])
def return_system_prompt():
    print("inside return_system_prompt")
  
    return jsonify({"system_prompt": interviewer_data["system_message"]})

@app.route('/chat_transcript', methods=['POST'])
def receive_transcript():
    chat_history = request.get_json()
    with open("chat_history.txt", "w") as f:
        for item in chat_history:
            if item["role"] == 'user':
                f.write(f"Interviewee: {item['content']}\n")
            elif item["role"] == 'assistant':
                f.write(f"Interviewer: {item['content']}\n")

    result = utils_interviwer.evaluate_transcript()
    utils_interviwer.send_transcript_and_result(email="jobinmathewsp@outlook.com", candidate_name=interviewer_data['candidate_name'], result=result)

    return jsonify({"return message": "Email Sent with the evaluation"})

if __name__ == '__main__':
    app.run(debug=True)