import {Grid} from "semantic-ui-react";
import './App.css';
import Login from "./components/authentication/Login";
import PageContainer from "./views/pageContainer/PageContainer";
import {Hub} from "aws-amplify";
import React, {useState, useEffect} from "react";
import { connect } from "react-redux";
import {updateLoginState} from "./actions/loginActions";



function App(props) {
    const {loginState, updateLoginState} = props;

    const [currentLoginState, updateCurrentLoginState] = useState(loginState);


    useEffect(() => {
        setAuthListener();
    }, []);

    useEffect(() => {
        updateCurrentLoginState(loginState);
    }, [loginState]);


    async function setAuthListener() {
        Hub.listen('auth', (data)=> {
            switch(data.payload.event) {
                case "signOut":
                    updateLoginState("signIn");
                    break;
                default:
                    break;
            }
        })
    }


    return (
      <Grid style={{width: "100vw", height: "100vh"}}>
        <Grid.Row style={{width: "100vw", height: "100vh"}}>
          <Grid.Column style={{width: "100vw", height: "100vh"}}>
              {
                  currentLoginState !== "signedIn" && (
                      /* Login component options:
                      *
                      * [logo: "custom", "none"]
                      * [type: "video", "image", "static"]
                      * [themeColor: "standard", "#012144" (color hex value in quotes) ]
                      *  Suggested alternative theme colors: #037dad, #5f8696, #495c4e, #4f2828, #ba8106, #965f94
                      * [animateTitle: true, false]
                      * [title: string]
                      * [darkMode (changes font/logo color): true, false]
                      * [disableSignUp: true, false]
                      * */
                      <Login logo={"custom"} type={"static"} themeColor={"standard"} animateTitle={false}
                             title={"Historical Audio Processing App"} darkMode={true}
                             disableSignUp={false}
                      />
                  )
              }
              {
                  currentLoginState === "signedIn" && (
                      <PageContainer />
                  )
              }
          </Grid.Column>
        </Grid.Row>
      </Grid>
  );
}

const mapStateToProps = (state) => {
    return {
        loginState: state.loginState.currentState,
    };
};

const mapDispatchToProps = {
    updateLoginState,
};

export default connect(mapStateToProps, mapDispatchToProps)(App);
