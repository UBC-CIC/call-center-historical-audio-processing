import React from 'react';
import {Segment, Header} from 'semantic-ui-react'
import MainTable from "./MainTable"
import {API, graphqlOperation} from 'aws-amplify'
import {listFeedbacks} from '../graphql/queries'
import {deleteFeedback} from '../graphql/mutations'


export default class Feedback extends React.Component {

    state = {feedbacks: []}

    async componentDidMount() {
        try {
            const apiData = await API.graphql(graphqlOperation(listFeedbacks))
            const feedbacks = apiData.data.listFeedbacks.items
            this.setState({feedbacks})
            console.log(feedbacks)
        } catch (err) {
            console.log('error: ', err)
        }
    }

    deleteFeedback = async (id) => {
        const feedback = {id: id}
        await API.graphql(graphqlOperation(deleteFeedback, {input: feedback}))
        this.componentDidMount()
        console.log("deleted")
    }

    render() {
        return (
            <div>
                <Segment>
                    <Header as='h1' textAlign="center">Feedback Hub</Header>
                </Segment>
                <Segment raised>
                    <MainTable inputData={this.state.feedbacks} deleteFeedback={this.deleteFeedback}/>
                </Segment>

            </div>
        )
    }
}

