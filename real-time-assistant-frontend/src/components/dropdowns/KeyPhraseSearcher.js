import React from "react";
import {Dropdown, Transition} from "semantic-ui-react";


export default class KeyPhraseSearcher extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            dropdownOptions: [],
            selectedValue: []
        };
        this.suggestedPhrases = []
        this.suggestedOptions = []
        this.manualOptions = []

        // Binding the functions to the instance
        this.handleManualKeyphraseAdd = this.handleManualKeyphraseAdd.bind(this)
        this.updateKeyphrases = this.updateKeyphrases.bind(this)
        this.getSelectedValue = this.getSelectedValue.bind(this)
        this.onChange = this.onChange.bind(this)
        this.toggleVisibility = this.toggleVisibility.bind(this)
    }

    /**
     * Handler that saves user added options into the dropdown
     * @param event - Event that triggers data entry
     * @param data - User added data
     */
    handleManualKeyphraseAdd(event, data) {
        this.manualOptions.push({key: data.value, value: data.value, text: data.value})
        this.setState({dropdownOptions: this.suggestedOptions.concat(this.manualOptions)})
    }

    /**
     * Updates the dropdown with a list of values that are passed in
     * @param keyphrases - List of values to add
     */
    updateKeyphrases(keyphrases) {
        let tempList = []
        for (let phrase of keyphrases) {
            tempList.push({key: phrase, value: phrase, text: phrase})
        }
        this.suggestedOptions = tempList
        this.suggestedPhrases = keyphrases
        this.setState({
            dropdownOptions: this.suggestedOptions.concat(this.manualOptions),
            selectedValue: this.suggestedPhrases
        })
        this.toggleVisibility()
    }

    /**
     * Returns the value(s) currently selected by the dropdown
     * @returns {string[]}
     */
    getSelectedValue() {
        return this.state.selectedValue
    }

    /**
     * Helper function to toggle glow animation
     */
    toggleVisibility() {
        this.setState((prevState) => ({visible: !prevState.visible}))
    }

    /**
     * Updates the dropdown value based on events
     * @param event - Event that adds data
     * @param data - Data to be added to the dropdown
     */
    onChange(event, data) {
        this.setState({selectedValue: data.value})
    }

    render() {
        //TODO Manual search button attached to the dropdown
        const {visible} = this.state
        return (
            <Transition visible={visible} animation='glow' duration={1500}>
                <Dropdown fluid multiple search selection scrolling
                          placeholder='Keyphrases'
                          allowAdditions={true}
                          value={this.state.selectedValue}
                          onAddItem={this.handleManualKeyphraseAdd}
                          options={this.state.dropdownOptions}
                          onChange={this.onChange}
                />
            </Transition>
        );
    }
}
