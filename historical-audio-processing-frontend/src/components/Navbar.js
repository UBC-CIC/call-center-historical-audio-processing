import React from 'react';
import { Menu, Segment } from 'semantic-ui-react';
import { Auth } from 'aws-amplify';
import { NavLink, withRouter } from 'react-router-dom';
import {AUTH_USER_ACCESS_TOKEN_KEY, AUTH_USER_ID_TOKEN_KEY} from '../constants/userConstant';
import { compose } from "redux";
import { connect } from "react-redux";
import { logout } from '../actions/AuthActions';
import { Cache } from 'aws-amplify';

class Navbar extends React.Component {
    constructor(props) {
        super(props);
        this.handleLogout = this.handleLogout.bind(this);
    }

    async handleLogout() {
        const { history } = this.props;
        try {
            await Auth.signOut({global: true});
            Cache.removeItem(AUTH_USER_ACCESS_TOKEN_KEY);
            Cache.removeItem(AUTH_USER_ID_TOKEN_KEY);
            this.props.logout();
            history.push('/login');
        } catch (e) {
            console.log('error signing out: ', e);
        }
    }

    render() {
        return (
            <Segment inverted color='green'>
                <Menu inverted secondary color='green'>
                    <Menu.Item
                        icon='home'
                        name='home'
                        as={NavLink} exact to='/main'
                    />
                    <Menu.Menu position='right'>
                        <Menu.Item
                            name='logout'
                            onClick={this.handleLogout}
                        />
                    </Menu.Menu>
                </Menu>
            </Segment>
        )
    }
}

const mapStateToProps = state => ({
    auth: state.authentication
});

export default compose(
    withRouter,
    connect(mapStateToProps, { logout })
)(Navbar);