import React from "react"
import { Button } from 'semantic-ui-react'

export default class DropDownButton extends React.Component {
    constructor(props){ 
        super(props);
        this.icon= props.icon
    }

    render() {
        return(
                <Button compact
                    onClick = {() => this.props.handleDropClick()}
                    circular icon={this.props.icon}
                />
        )
    }
}