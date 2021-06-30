import requests

# file is a Bytes64 object
def getReziScore(file):
    if file:
        url = 'https://us-central1-rezi-3f268.cloudfunctions.net/scoreFromFile/'
        response = requests.post(url, files={"resume": ('resume.pdf', file.getvalue(), 'application/pdf')})
        if (response.status_code == requests.codes.ok):
            return response.text
        else:
            raise ValueError("Could not fetch your score!")
    else:
        raise FileExistsError("Resume file not found!")
