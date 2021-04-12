import React from "react";
import {Button} from "semantic-ui-react";


export default class FeedbackButton extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            buttonEnabled: props.buttonEnabled,
            handleClick: props.onClick
        }
        this.enableFeedbackButton = this.enableFeedbackButton.bind(this)
    }

    /**
     * Third step in enabling the feedback button
     *
     *   SubmitButton.handleClick() ->
     *   App.enableFeedbackButton() ->
     * **FeedbackButton.enableFeedbackButton()**
     */
    enableFeedbackButton() {
        this.setState({
            buttonEnabled: true
        })
    }


    render() {
        return (
            <Button disabled={!this.state.buttonEnabled} basic={!this.state.buttonEnabled}
                    color='teal' onClick={this.state.handleClick}>
                Post-Call Feedback
            </Button>
        );
    }

}