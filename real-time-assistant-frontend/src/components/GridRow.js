import React from "react"
import {Grid, Label, Icon} from 'semantic-ui-react'
import AcceptCancelButton from './buttons/AcceptDiscardButton'
import DropDownButton from './buttons/DropDownButton'

export default class GridRow extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            expanded: props.expanded,
            dropIcon: 'angle double down',
            expandedDetails: <div></div>,
        }
        this.document = {
            "jurisdiction": this.props.Jurisdiction,
            "key_phrases": this.props.Keyphrases,
            "procedure": this.props.SOP,
            "transcript": this.props.CallerTranscript
        }

        this.handleApproveClick = this.props.handleApproveClick
        this.handleDiscardClick = this.props.handleDiscardClick
        this.handleDropClick = this.handleDropClick.bind(this)
        this.iconSelector = this.iconSelector.bind(this)
        this.renderFeedbackDetails = this.renderFeedbackDetails.bind(this)

    }


    iconSelector() {
        if (this.props.FeedbackType === "accurate") {
            this.icon = "check circle"
            this.iconColor = "green"
        } else if (this.props.FeedbackType === "acceptable") {
            this.icon = "warning circle"
            this.iconColor = "yellow"
        } else if (this.props.FeedbackType === "inaccurate") {
            this.icon = "times circle"
            this.iconColor = "red"
        } else {
            console.log(this.props.FeedbackType)
            this.icon = "question circle"
            this.iconColor = "blue"
        }

        return (
            <Grid.Column textAlign='left'>
                <Icon size="large" color={this.iconColor} name={this.icon}/>
                {this.props.FeedbackType}
            </Grid.Column>
        )

    }


    handleDropClick() {

        this.setState(prevState => {
            if (prevState.expanded === "false") {
                return {
                    expanded: "true",
                    dropIcon: 'angle double down',
                    expandedDetails: <div></div>
                }
            } else {
                const KeyphrasesSeperated = this.props.Keyphrases.map(phrase => <Label>{phrase}</Label>)
                return {
                    expanded: "false",
                    dropIcon: 'angle double up',
                    expandedDetails:
                        <Grid.Row columns={4} divided>
                            <Grid.Column width={1}></Grid.Column>
                            <Grid.Column>
                                {this.renderFeedbackDetails(this.props.FeedbackDetails)}
                                <h5>Key Phrases</h5>
                                {KeyphrasesSeperated}
                            </Grid.Column>
                            <Grid.Column>
                                <h5>Caller Transcript</h5>
                                {this.props.CallerTranscript}
                            </Grid.Column>
                            <Grid.Column textAlign={'center'}>
                                <h5>Callee Transcript</h5>
                                {this.props.CalleeTranscript}
                            </Grid.Column>
                        </Grid.Row>


                }
            }

        })
    }

    renderFeedbackDetails(text) {
        if (text === "") {
            return <div/>
        } else {
            return (
                <div>
                    <h5>Feedback Details</h5>
                    {this.props.FeedbackDetails}
                </div>
            );
        }
    }

    render() {
        console.log(this.props.Keyphrases)
        return (
            <Grid celled>
                <Grid.Row textAlign="center" columns={6} divided="vertically">

                    <Grid.Column width={1}>
                        <DropDownButton icon={this.state.dropIcon} handleDropClick={this.handleDropClick}
                                        expanded={this.state.expanded}/>
                    </Grid.Column>
                    <Grid.Column width={3}>
                        <AcceptCancelButton handleApproveClick={this.handleApproveClick} document={this.document}
                                            handleDiscardClick={this.handleDiscardClick} id={this.props.id}/>
                    </Grid.Column>
                    <Grid.Column>
                        {this.props.ContactId}
                    </Grid.Column>
                    <Grid.Column>
                        {this.props.SOP}
                    </Grid.Column>
                    <Grid.Column>
                        {this.props.Jurisdiction}
                    </Grid.Column>

                    {this.iconSelector()}


                </Grid.Row>
                {this.state.expandedDetails}

            </Grid>


        )

    }

}
