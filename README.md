# ECOMM 911 Connect Virtual Assistant

## Project Summary

The Ecomm 911 Connect Virtual Assistant tool serves to assist non-emergency call takers in identifying the nature and scenario of incoming calls and moving ahead with the correct standard procedures, leading to increase in overall efficiency and accuracy in call-taking. Procedure recommendations are based on document similarity in ElasticSearch between the currently transcribed call and transcripts of audio call files provided by the user. 

## High-level Architecture

![alt text](./images/ecomm911-AWS-diagram.png)

## Stack Documentation and Deployment Guides

[Frontend Deployment](./frontend-doc.md)\
[Audio Transcription Stack Deployment](./backend/transcript-indexer/README.md)\
[AWS Connect Call Transcription Stack Deployment](./backend/connect-virtual-assistant/README.md)

## Credits
This proof of concept was coded and architected by Colin Zhang, with guidance from the UBC CIC tech and project teams and with quoted usage and reference to some AWS sample template projects. 
