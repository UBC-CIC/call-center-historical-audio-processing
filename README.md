# E-Comm 911 Connect Virtual Assistant

## Project Summary

The E-Comm 911 Connect Virtual Assistant tool serves to assist non-emergency call takers in identifying the nature and 
scenario of incoming calls and moving ahead with the correct standard procedures, leading to increase in overall 
efficiency and accuracy in call-taking. Procedure recommendations are based on keyphrase similarity in ElasticSearch 
between the currently transcribed call and transcripts of audio call files provided by the user. 

## High-level Architecture

![alt text](documentation_images/ecomm911-AWS-diagram.png)

## Stack Documentation and Deployment Guides

[Audio Processing Backend Stack Deployment](audio-processing-backend/README.md)\
[Audio Processing Frontend Stack Deployment](audio-processing-frontend/README.md)\
[Virtual Assistant Backend Stack Deployment](real-time-assistant-backend/README.md)\
[Virtual Assistant Frontend Stack Deployment](real-time-assistant-frontend/README.md)

## Credits
This proof of concept was coded and architected by Colin Zhang, with guidance from the UBC CIC tech and project teams 
and with quoted usage and reference to some AWS sample template projects.

## License
This project is distributed under the [MIT License](./LICENSE).
