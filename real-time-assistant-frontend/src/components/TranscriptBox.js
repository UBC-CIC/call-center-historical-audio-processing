import React from 'react';
import {Transition} from "semantic-ui-react";

export default class TranscriptBox extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            visible: true,
            boxData:
                <div>
                    {props.transcript}
                </div>
        };

        // Binding the functions to the instance
        this.toggleVisibility = this.toggleVisibility.bind(this)
        this.updateTranscript = this.updateTranscript.bind(this)
    }

    /**
     * Helper function to toggle glow animation
     */
    toggleVisibility() {
        this.setState((prevState) => ({visible: !prevState.visible}))
    }

    /**
     * Updates the component state with the new transcript boxData so it can be re-drawn
     * also triggers a glow animation
     * @param newTranscript
     */
    updateTranscript(newTranscript) {
        this.setState({
            boxData: newTranscript
        })
        this.toggleVisibility()
    }


    render() {
        const {visible} = this.state
        return (
            <Transition visible={visible} animation='glow' duration={1500}>
                <div>
                    {this.state.boxData}
                </div>
            </Transition>
        );
    }
}
