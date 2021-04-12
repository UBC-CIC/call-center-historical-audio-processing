import React from "react";
import {Button} from "semantic-ui-react";


export default class SOPButton extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            enabled: props.enabled,
            SOP: props.SOP,

        };
        this.dropdown = props.procedureDropdown
        this.enableFeedbackButton = this.props.enableFeedbackButton
        this.toggleButton = this.toggleButton.bind(this)
        this.handleClick = this.handleClick.bind(this)
    }

    /**
     * Toggles the submit button between enabled and disabled state
     * @param val
     */
    toggleButton(val) {
        this.setState({
            enabled: val
        })
    }

    /**
     * Enables and updates the value of the SOP button text based on input
     * if the input is an empty string (which is passed when the dropdown connect button is cleared,
     * it reverts the button label to the original text
     * @param val - Value to update button label with
     */
    updateButton(val) {
        if(val === '....') {
            // case for default value for when resetting button
            this.setState({
                enabled: false,
                SOP: val
            })
        } else if(val !== '') {
            this.setState({
                enabled: true,
                SOP: val
            })
        } else {
            this.setState({
                enabled: false,
                SOP: 'Fetch SOP'
            })
        }
    }

    /**
     * Click handler for the submit button
     */
    handleClick() {
        // TODO Submit button will fetch SOP document via API call from somewhere
        // Use this.state.SOP to make the relevant API call
        this.enableFeedbackButton()
        console.log(this.state.SOP)
    }

    render() {
        return (
            <Button basic={!this.state.enabled}
                    disabled={!this.state.enabled}
                    color={'red'}
                    onClick={this.handleClick}>
                {this.state.SOP}
            </Button>
        );
    }
}