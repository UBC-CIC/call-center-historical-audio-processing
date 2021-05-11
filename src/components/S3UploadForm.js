import React from "react";
import { Route, withRouter } from "react-router-dom";
import {
  Form,
  Button,
  Input,
  Grid,
  Header,
  Segment,
  Message,
  TextArea,
} from "semantic-ui-react";
import { Storage, API, graphqlOperation } from "aws-amplify";
import { v4 as uuidv4 } from "uuid";

import awsExports from "../aws-exports";
import { createTranscript } from "../graphql/mutations";

const listOfFiles = [];

const initialState = {
  currentFile: null,
  currentFileName: "",
  currentFileType: "",
  SOP: "",
  jurisdiction: "",
  description: "",
  invalidFileType: false,
  submitSuccess: false,
};

class S3UploadForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      jurisdiction: "",
      SOP: "",
      description: "",
      listOfFiles: [],
      submitSuccess: false,
      invalidFiles: [],
    };

    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.handleFileChange = this.handleFileChange.bind(this);
  }

  async handleSubmit() {
    
    let SOP = this.state.SOP;
    let jurisdiction = this.state.jurisdiction;
    let description = this.state.description;
    for (
      var fileNumber = 0;
      fileNumber < this.state.listOfFiles.length;
      fileNumber++
    ) {
      const uuid = uuidv4();
      var currentFile = this.state.listOfFiles[fileNumber.toString(10)];
      console.log(currentFile);

      let fileName = currentFile.name;
      let fileType = currentFile.type;
      const key = SOP.concat("/" + uuid)
        .concat("_")
        .concat(fileName);
      try {
        await Storage.put(key, currentFile.entireFile, {
          metadata: {
            SOP: SOP,
            jurisdiction: jurisdiction,
            description: description,
            fileName: fileName,
            fileType: fileType,
          },
        });

        // write to dynamoDB transcript Table
        const bucketName = awsExports.aws_user_files_s3_bucket;
        const bucketKey = "public/" + key;
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
            bucketKey: bucketKey,
          },
        };
        await API.graphql(
          graphqlOperation(createTranscript, { input: audioItem })
        );

        let nextState = initialState;
        nextState["submitSuccess"] = true;
        this.setState(nextState);
      } catch (e) {
        console.log(e);
      }
    }
  }

  handleChange(e) {
    const { name, value } = e.target;
    this.setState({
      [name]: value,
    });
  }

  handleFileChange(e) {
    let filesList = e.target.files;
    let allValidFiles = [];
    let invalidFileNames = [];

    for (var fileNumber = 0; fileNumber < filesList.length; fileNumber++) {
      var file = filesList[fileNumber.toString(10)];

      var currentFile = {};
      currentFile.name = file.name;

      currentFile.type = file.type;
      currentFile.fileExt = file.name.split(".").pop();

      let fileExts = ["wav", "mp3", "mp4", "flac"];
      if (fileExts.indexOf(currentFile.fileExt) !== -1) {
        currentFile.entireFile = file;
        currentFile.invalidFileType = false;
        currentFile.submitSuccess = false;
        allValidFiles = [...allValidFiles, currentFile];
      } else {
        currentFile.invalidFileType = true;
        invalidFileNames = [...invalidFileNames, currentFile.name];
      }
    }

    this.setState({
      listOfFiles: allValidFiles,
      invalidFiles: invalidFileNames,
    });
  }

  render() {
    return (
      <Grid
        textAlign="center"
        style={{ height: "100vh" }}
        verticalAlign="middle"
      >
        <Grid.Column style={{ maxWidth: 400 }}>
          <Segment>
            <Header as="h2" textAlign="center">
              Upload Call Audio File
            </Header>
            <Form onSubmit={this.handleSubmit}>
              <Form.Field>
                <input
                  type="file"
                  multiple
                  onChange={(e) => this.handleFileChange(e)}
                />
              </Form.Field>
              <Form.Field
                fluid
                inline
                control={Input}
                name="SOP"
                label="SOP"
                value={this.state.SOP}
                onChange={this.handleChange}
              />
              <Form.Field
                fluid
                inline
                control={Input}
                name="jurisdiction"
                label="Jurisdiction"
                value={this.state.jurisdiction}
                onChange={this.handleChange}
              />
              <Form.Field
                fluid
                inline
                control={TextArea}
                name="description"
                label="Description"
                value={this.state.description}
                onChange={this.handleChange}
              />
              <Form.Button
                color={"green"}
                content="Submit"
                disabled={
                  !this.state.listOfFiles ||
                  !this.state.SOP ||
                  !this.state.description ||
                  !this.state.jurisdiction
                }
              />
            </Form>
          </Segment>
          {!!this.state.invalidFiles.length && (
            <Message negative>
              <p>Unsupported file type(s)</p>
              {this.state.invalidFiles.map((fileName) => (
                <li>{fileName} </li>
              ))}
            </Message>
          )}
          {!!this.state.submitSuccess && (
            <Message positive>
              <p>
                File successfully uploaded! Transcription job for the audio file
                will be started.
              </p>
            </Message>
          )}
        </Grid.Column>
      </Grid>
    );
  }
}

export default withRouter(S3UploadForm);
