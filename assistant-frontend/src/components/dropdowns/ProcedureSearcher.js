import React from "react";
import {Dropdown, Transition} from "semantic-ui-react";
import {PROCEDURES} from "../Constants";


export default class ProcedureSearcher extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            selectedValue: '',
            visible: true
        }
        // Filling up the procedures dropdown options with pre-defined values
        this.procedureOptions = []
        for (let procedure of PROCEDURES) {
            this.procedureOptions.push({
                key: procedure.key,
                value: procedure.key,
                text: procedure.key,
                description: procedure.text
            })
        }
        this.onDropdownSet = props.onDropdownSet

        // Binding the functions to the instance
        this.updateProcedure = this.updateProcedure.bind(this)
        this.getSelectedValue = this.getSelectedValue.bind(this)
        this.onChange = this.onChange.bind(this)
        this.toggleVisibility = this.toggleVisibility.bind(this)
    }

    /**
     * Function to autofill the dropdown selected value with a glow animation
     * @param procedure - Value to update the dropdown with
     */
    updateProcedure(procedure) {
        this.setState({selectedValue: procedure})
        this.toggleVisibility()
    }

    /**
     * Returns a string value of the selected procedure
     * @returns {string}
     */
    getSelectedValue() {
        return this.state.selectedValue
    }

    /**
     * Handler to re-draw selected value change for the dropdown
     * Calls another handler in AssistantWindow to update the manual SOP fetch button
     * @param event
     * @param data
     */
    onChange(event, data) {
        this.setState({selectedValue: data.value})
        this.onDropdownSet(data.value)
    }

    /**
     * Helper function for glow animation
     */
    toggleVisibility() {
        this.setState((prevState) => ({visible: !prevState.visible}))
    }

    render() {
        const {visible} = this.state
        return (
            <Transition visible={visible} animation='glow' duration={1500}>
                <Dropdown search clearable selection fluid
                          placeholder='SOP'
                          value={this.state.selectedValue}
                          selectOnBlur={false}
                          options={this.procedureOptions}
                          onChange={this.onChange}
                />
            </Transition>
        );
    }
}

