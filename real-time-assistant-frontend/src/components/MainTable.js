import React from "react"
import {Grid} from 'semantic-ui-react'
import GridRow from "./GridRow"
import indexDocument from "./ElasticSearchService";


export default class MainGrid extends React.Component {

    constructor(props) {
        super(props)
        this.state = {
            callData: props.inputData
        }
        this.handleApproveClick = this.handleApproveClick.bind(this)
        this.handleDiscardClick = this.handleDiscardClick.bind(this)
        this.deleteRow = this.deleteRow.bind(this)
    }

    deleteRow(id) {
        this.props.deleteFeedback(id)
        console.log(id)
    }

    handleApproveClick(id, document) {
        indexDocument(id, document).then(() => console.log("success in re-indexing")).catch((err) => console.log(err))
        // this.deleteRow(id)
    }

    handleDiscardClick(id) {
        this.deleteRow(id)
    }

    render() {
        console.log(this.props.inputData)
        const callDataList = this.props.inputData.map(call =>
            <GridRow
                id={call.id}
                ContactId={call.ContactId}
                SOP={call.SOP}
                FeedbackType={call.FeedbackType}
                FeedbackDetails={call.FeedbackDetails}
                CallerTranscript={call.CallerTranscript}
                CalleeTranscript={call.CalleeTranscript}
                Keyphrases={call.Keyphrases}
                Jurisdiction={call.Jurisdiction}
                handleApproveClick={this.handleApproveClick}
                handleDiscardClick={this.handleDiscardClick}
            />)

        return (
            <div>
                <Grid celled divided>
                    <Grid.Row textAlign='center' columns={6}>
                        <Grid.Column width={1}/>
                        <Grid.Column width={3}><h3>Status</h3></Grid.Column>
                        <Grid.Column><h3>Call ID</h3></Grid.Column>
                        <Grid.Column><h3>SOP</h3></Grid.Column>
                        <Grid.Column><h3>Jurisdiction</h3></Grid.Column>
                        <Grid.Column><h3>Feedback</h3></Grid.Column>
                    </Grid.Row>

                </Grid>
                {callDataList}

            </div>
        );
    }

}
