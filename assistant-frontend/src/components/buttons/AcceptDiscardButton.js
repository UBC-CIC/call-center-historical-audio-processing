import React from "react"
import { Button } from 'semantic-ui-react'

export default class AcceptDiscardButton extends React.Component {

    render() {
        return(
            <Button.Group compact>
                <Button
                    color ="green"
                    onClick = {() => this.props.handleApproveClick(this.props.id, this.props.document)}
                    >Approve</Button>
                <Button 
                    color = "red"
                    onClick = {() => this.props.handleDiscardClick(this.props.id)}
                >Discard</Button>
            </Button.Group>
        )
    }
}

