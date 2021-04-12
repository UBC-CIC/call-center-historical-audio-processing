import React from 'react';
import '../styles/App.css';
import {Button, Form, Grid, Segment, TextArea} from 'semantic-ui-react';
import AssistantWindow from './AssistantWindow';
import FeedbackButton from "./buttons/FeedbackButton";
import CallWindow from "./CallWindow";
import {AmplifySignOut} from "@aws-amplify/ui-react";
import {createFeedback} from "../graphql/mutations";
import {API} from "aws-amplify";
import AssistantWindowState from "./AssistantWindowState";


/**
 * The entire virtual assistant page, contains 4 functionalities in 4 segments.
 * The first allows to pick a live call.
 * The second is the virtual assistant menu with the call features, and the ability to submit SOP and jurisdiction.
 * The third is a post-call feedback button enabled after the call.
 * The fourth is the feedback input segment only brought into view after feedback button click.
 */
export default class AssistantApp extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            calls: [],
            hasCallEnded: false,
            feedbackSegment: <div/>,
            incorrectFeedbackDetailsForm: <div/>
        };
        /**
         * Variable to hold the state of the assistant window
         * This property holds all the metadata of a specific call that is selected, it is passed
         * down to sub-components where necessary and updated there as well. After the call is over, this
         * object will have upto-date information on call metadata
         */
        this.assistantState = new AssistantWindowState()

        //Refs to access child components
        this.assistantWindow = React.createRef()
        this.feedbackButton = React.createRef()

        // Binding the AssistantApp instance to its functions
        this.handleCallerIDSet = this.handleCallerIDSet.bind(this)
        this.enableFeedbackButton = this.enableFeedbackButton.bind(this)
        this.handleFeedbackClick = this.handleFeedbackClick.bind(this)
        this.handleIncorrectFeedback = this.handleIncorrectFeedback.bind(this)
        this.handleIncorrectFeedbackSubmit = this.handleIncorrectFeedbackSubmit.bind(this)
        this.handleAmbiguousFeedback = this.handleAmbiguousFeedback.bind(this)
        this.handleCorrectFeedback = this.handleCorrectFeedback.bind(this)
    }

    /**
     * Called after a callID is set in the call dropdown in CallWindow.js
     * Used to update the assistant window (a separate component) with call contents and extracted features
     * @param callerID - Call to view information from
     */
    handleCallerIDSet(callerID) {
        this.assistantState.contactId = callerID
        this.assistantWindow.current.updateAssistantWindow(callerID)
    }

    /**
     * Second step in enabling the feedback button
     *
     *   SOPButton.handleClick()   ->
     * **AssistantApp.enableFeedbackButton()** ->
     *   FeedbackButton.enableFeedbackButton()
     */
    enableFeedbackButton() {
        this.setState({
            hasCallEnded: true
        })
        this.feedbackButton.current.enableFeedbackButton()
    }

    handleFeedbackClick() {
        this.setState({
            feedbackSegment:
                <div>
                    <Segment>
                        <Button color={'orange'} onClick={this.handleIncorrectFeedback}>
                            Prediction is completely off
                        </Button>
                        <Button color={'olive'} onClick={this.handleAmbiguousFeedback}>
                            Prediction is acceptable
                        </Button>
                        <Button color={'green'} onClick={this.handleCorrectFeedback}>
                            Prediction is spot on
                        </Button>
                    </Segment>
                </div>
        });
    }

    handleIncorrectFeedback() {
        let feedbackDetails = ""
        this.setState({
            incorrectFeedbackDetailsForm:
                <Segment>
                    <Form>
                        <TextArea onChange={(event, data)=> {
                            feedbackDetails = data.value
                        }}
                                  placeholder='Please explain what went wrong'/>
                        <br/>
                        <Form.Button onClick={()=> {
                            console.log(feedbackDetails);
                            this.assistantState.feedbackDetails = feedbackDetails
                            this.handleIncorrectFeedbackSubmit()
                        }}>
                            Submit Feedback</Form.Button>
                    </Form>
                </Segment>
        })
    }

    handleIncorrectFeedbackSubmit() {
        API.graphql({
            query: createFeedback, variables: {
                input: {
                    ContactId: this.assistantState.contactId,
                    FeedbackType: "inaccurate",
                    FeedbackDetails: this.assistantState.feedbackDetails,
                    CallerTranscript: this.assistantState.callerTranscript,
                    CalleeTranscript: this.assistantState.calleeTranscript,
                    Keyphrases: this.assistantState.keyphrases,
                    SOP: this.assistantState.firstSOP,
                    Jurisdiction: this.assistantState.jurisdiction
                }
            }
        })
    }

    handleAmbiguousFeedback() {
        API.graphql({
            query: createFeedback, variables: {
                input: {
                    ContactId: this.assistantState.contactId,
                    FeedbackType: "acceptable",
                    FeedbackDetails: this.assistantState.feedbackDetails,
                    CallerTranscript: this.assistantState.callerTranscript,
                    CalleeTranscript: this.assistantState.calleeTranscript,
                    Keyphrases: this.assistantState.keyphrases,
                    SOP: this.assistantState.firstSOP,
                    Jurisdiction: this.assistantState.jurisdiction
                }
            }
        })
    }

    handleCorrectFeedback() {
        API.graphql({
            query: createFeedback, variables: {
                input: {
                    ContactId: this.assistantState.contactId,
                    FeedbackType: "accurate",
                    FeedbackDetails: this.assistantState.feedbackDetails,
                    CallerTranscript: this.assistantState.callerTranscript,
                    CalleeTranscript: this.assistantState.calleeTranscript,
                    Keyphrases: this.assistantState.keyphrases,
                    SOP: this.assistantState.firstSOP,
                    Jurisdiction: this.assistantState.jurisdiction
                }
            }
        })
    }

    render() {
        return (
            <div className="App">
                <Grid textAlign='center' style={{height: '100vh'}} verticalAlign='middle'>
                    <Grid.Column style={{maxWidth: 1200}}>
                        <Segment>
                            <CallWindow onCallerIDSet={this.handleCallerIDSet}/>
                        </Segment>
                        <Segment>
                            <AssistantWindow ref={this.assistantWindow}
                                             enableFeedbackButton={this.enableFeedbackButton}
                                             stateHolder={this.assistantState}
                            />
                        </Segment>
                        <Segment>
                            <FeedbackButton ref={this.feedbackButton}
                                            buttonEnabled={this.state.hasCallEnded}
                                            onClick={this.handleFeedbackClick}/>
                        </Segment>
                        {this.state.feedbackSegment}
                        {this.state.incorrectFeedbackDetailsForm}
                        <Segment>
                            <AmplifySignOut/>
                        </Segment>
                    </Grid.Column>
                </Grid>
            </div>
        );
    }
}


