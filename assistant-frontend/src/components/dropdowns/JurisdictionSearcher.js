import React from "react";
import {Dropdown, Transition} from "semantic-ui-react";
import {JURISDICTIONS} from "../Constants";


export default class JurisdictionSearcher extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            selectedValue: '',
            visible: true
        }
        this.jurisdictionOptions = []

        // Filling up the jurisdictions dropdown options with pre-defined values
        for (let jurisdiction of JURISDICTIONS) {
            this.jurisdictionOptions.push({
                key: jurisdiction.key, value: jurisdiction.key,
                text: jurisdiction.key, description: jurisdiction.value
            })
        }

        this.onDropdownSet = props.onDropdownSet
        // Binding the functions to the instance
        this.updateJurisdiction = this.updateJurisdiction.bind(this)
        this.getSelectedValue = this.getSelectedValue.bind(this)
        this.onChange = this.onChange.bind(this)
        this.toggleVisibility = this.toggleVisibility.bind(this)
    }

    /**
     * Updates the selected value dropdown value and creating a glow transition animation
     * @param jurisdiction - Value to update the dropdown with
     */
    updateJurisdiction(jurisdiction) {
        this.setState({selectedValue: jurisdiction})
        this.toggleVisibility()
    }

    /**
     * Returns the string of the selected dropdown value
     * @returns {string}
     */
    getSelectedValue() {
        return this.state.selectedValue
    }

    /**
     * Handler to re-draw dropdown when value filled via UI
     * Also calls a handler in AssistantWindow to pass the selected value there
     * @param event
     * @param data
     */
    onChange(event, data) {
        this.setState({selectedValue: data.value})
        this.onDropdownSet(data.value)
    }

    /**
     * Helper function for the glow transition animation
     */
    toggleVisibility() {
        this.setState((prevState) => ({visible: !prevState.visible}))
    }

    render() {
        const {visible} = this.state
        return (
            <Transition visible={visible} animation='glow' duration={1500}>
                <Dropdown search fluid selection clearable
                          placeholder='Jurisdiction'
                          value={this.state.selectedValue}
                          selectOnBlur={false}
                          options={this.jurisdictionOptions}
                          onChange={this.onChange}/>
            </Transition>
        );
    }
}
