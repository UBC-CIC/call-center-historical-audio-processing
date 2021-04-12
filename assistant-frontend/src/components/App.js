import Amplify from "aws-amplify";
import config from "../aws-exports";
import {withAuthenticator} from "@aws-amplify/ui-react";
import React from "react";
import {BrowserRouter as Router, Switch, Route, Link} from "react-router-dom";
import AssistantApp from "./AssistantApp";
import Feedback from "./Feedback"
import {Menu} from "semantic-ui-react";

Amplify.configure(config);

class App extends React.Component {
    render() {
        let navbarState = ''
        return (
            <div>
                <Router>
                    <div align={'center'}>
                        <Menu widths={4}>
                            <Menu.Item
                                active={navbarState === 'Assistant App'}
                                color={'blue'}
                                // onClick={()=> this.navbarState='Assistant App'}
                            >
                                <Link to="/assistantApp/">Assistant App</Link>
                            </Menu.Item>
                            <Menu.Item
                                active={navbarState === 'Feedback App'}
                                color={'red'}
                            >
                                <Link to="/feedbackApp/">Feedback App</Link>
                            </Menu.Item>
                        </Menu>
                        <Switch>
                            <Route exact path="/assistantApp/">
                                <AssistantApp/>
                            </Route>
                            <Route exact path="/feedbackApp/">
                                <Feedback/>
                            </Route>
                        </Switch>
                    </div>
                </Router>
            </div>
        );
    }
}

export default withAuthenticator(App);