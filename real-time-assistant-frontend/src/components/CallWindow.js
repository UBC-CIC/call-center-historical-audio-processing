import React from 'react';
import {Button, Dropdown, Grid, Icon} from 'semantic-ui-react';
import {DynamoDBClient, ScanCommand} from "@aws-sdk/client-dynamodb";
import {unmarshall} from "@aws-sdk/util-dynamodb";
import {Auth} from "aws-amplify";
import config from "../aws-exports";


const queryParams = {
    TableName: 'contactDetails',
    ProjectionExpression: 'ContactId'
}

/**
 * UI Component that fetches the list of live calls from DynamoDB, allows selection
 * of a particular call, and forwards that callID to the AssistantWindow for further
 * call information querying
 */
export default class CallWindow extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            callDropdownOptions: [],
            handleCallerIDSet: props.onCallerIDSet
        }
        this.callerIDS = []

        this.refreshClick = this.refreshClick.bind(this)
        this.onDropdownValueSet = this.onDropdownValueSet.bind(this)
    }

    /**
     * Uses the DynamoDB scan call to get all ContactId's from the ContactDetails Table
     * Parses the result and returns a string list of callerId's
     * Async function that returns a promise
     * @returns list of callerIDs
     */
    getCallerIDS() {
        return Auth.currentCredentials()
            .then((credentials) => {
                return new DynamoDBClient({
                    region: config.aws_project_region,
                    credentials: credentials
                });
            }).then((client) => {
                return client.send(new ScanCommand(queryParams))
            }).then((result) => {
                return result.Items.map((Item) => unmarshall(Item).ContactId)
            }).catch((err) => {
                console.log(err)
            });

    }

    /**
     * Function that gets the list of callerIDS from DynamoDB and populates the call dropdown list with it
     */
    refreshClick() {
        let that = this
        this.callerIDS = []
        this.getCallerIDS().then((callList) => {
            for (let callerID of callList) {
                that.callerIDS.push({
                    key: callerID,
                    value: callerID,
                    text: callerID
                })
            }
            that.setState({
                callDropdownOptions: that.callerIDS
            });
        }).catch(err => {
            console.log(err)
        })
    }

    /**
     * Handler for change in the dropdown
     * Sets the value that is clicked
     * @param event - event that triggers the change (e.g mouseclick)
     * @param data - data that is modified by the event
     */
    onDropdownValueSet(event, data) {
        this.state.handleCallerIDSet(data.value)
    }


    render() {
        return (
            <Grid columns={2} divided textAlign='center'>
                <Grid.Row>
                    <Dropdown placeholder='Live Call ID'
                              onChange={this.onDropdownValueSet}
                              options={this.state.callDropdownOptions}
                              search selection/>
                    <Button secondary icon onClick={this.refreshClick}>
                        <Icon name={'sync'}/>
                    </Button>
                </Grid.Row>
            </Grid>
        );
    }
}