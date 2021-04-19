import React from 'react';
import {withRouter} from 'react-router-dom';
import {Form, Input, Grid, Header, Segment, Message, TextArea} from 'semantic-ui-react';
import {Storage, API, graphqlOperation} from 'aws-amplify';
import { v4 as uuidv4 } from 'uuid';

import awsExports from '../aws-exports';
import { createTranscript } from '../graphql/mutations';

const initialState = {
    currentFile: null,
    currentFileName: '',
    currentFileType: '',
    SOP: '',
    jurisdiction: '',
    description: '',
    invalidFileType: false,
    submitSuccess: false
}

class S3UploadForm extends React.Component {
    constructor(props) {
        super(props);
        this.state = initialState;

        this.handleSubmit = this.handleSubmit.bind(this);
        this.handleChange = this.handleChange.bind(this);
        this.handleFileChange = this.handleFileChange.bind(this);
    }

    async handleSubmit() {
        const uuid = uuidv4();
        let SOP = this.state.SOP;
        let jurisdiction = this.state.jurisdiction;
        let description = this.state.description;
        let fileName = this.state.currentFileName;
        let fileType = this.state.currentFileType;
        const key = SOP.concat('/'+uuid).concat('_').concat(fileName);
        try {
            await Storage.put(key, this.state.currentFile, {
                metadata: {
                    SOP: SOP,
                    jurisdiction: jurisdiction,
                    description: description,
                    fileName: fileName,
                    fileType: fileType
                }
            });
    
            // write to dynamoDB transcript Table
            const bucketName = awsExports.aws_user_files_s3_bucket;
            const bucketKey = 'public/' + key;
            const time = Math.round(Date.now() / 1000) + 6 * 3600; // 6 hour TTL
            const audioItem = {
                id: uuid,
                description: description,
                jurisdiction: jurisdiction,
                fileType: fileType,
                fileName: fileName,
                procedure: SOP,
                expireTime: time,
                fileData: {
                    bucketName: bucketName,
                    bucketKey: bucketKey
                }
            }
            await API.graphql(graphqlOperation(createTranscript, {input:audioItem}));

            let nextState = initialState;
            nextState['submitSuccess'] = true; 
            this.setState(nextState);
        } catch(e) {
            console.log(e);
        }
    }

    handleChange(e) {
        const {name, value} = e.target;
        this.setState({
            [name]: value,
            submitSuccess: false
        });
    }

    handleFileChange(e) {
        const file = e.target.files[0];
        const name = file.name;
        const type = file.type;
        const fileExt = name.split('.').pop();
        let fileExts = ['wav', 'mp3', 'mp4', 'flac'];
        if (fileExts.indexOf(fileExt) !== -1) {
            this.setState({
                currentFile: file,
                currentFileName: name,
                currentFileType: type,
                invalidFileType: false,
                submitSuccess: false
            });
        } else {
            this.setState({invalidFileType: true});
        }
    }

    render() {
        return (
            <Grid textAlign='center' style={{ height: '100vh' }} verticalAlign='middle'>
                <Grid.Column style={{ maxWidth: 400 }}>
                    <Segment>
                        <Header as='h2' textAlign='center'>
                            Upload Call Audio File
                        </Header>
                        <Form onSubmit={this.handleSubmit}>
                            <Form.Field
                                fluid
                                control={Input}
                                type={'file'}
                                onChange={this.handleFileChange}
                            />
                            <Form.Field
                                fluid
                                inline
                                control={Input}
                                name='SOP'
                                label='SOP'
                                value={this.state.SOP}
                                onChange={this.handleChange}
                            />
                            <Form.Field
                                fluid
                                inline
                                control={Input}
                                name='jurisdiction'
                                label='Jurisdiction'
                                value={this.state.jurisdiction}
                                onChange={this.handleChange}
                            />
                            <Form.Field
                                fluid
                                inline
                                control={TextArea}
                                name='description'
                                label='Description'
                                value={this.state.description}
                                onChange={this.handleChange}
                            />
                            <Form.Button color={'green'} content='Submit'
                            disabled={!this.state.currentFile || !this.state.SOP || !this.state.description || !this.state.jurisdiction}/>
                        </Form>
                    </Segment>
                    {!!this.state.invalidFileType &&
                    <Message negative>
                        <p>Unsupported file type detected.</p>
                    </Message>}
                    {!!this.state.submitSuccess &&
                    <Message positive>
                        <p>File successfully uploaded! Transcription job for the audio file will be started.</p>
                    </Message>}
                </Grid.Column>
            </Grid>
            );
    }
}

export default withRouter(S3UploadForm);