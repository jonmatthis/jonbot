import React from 'react';
import logo from './logo.svg';
import './App.css';

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      data: null
    };
  }

  componentDidMount() {
    fetch('manifest.json', {
      headers : {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
       }
    })
    .then(response => response.json())
    .then(jsonData => this.setState({ data: jsonData }));
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h1>Data from JSON file:</h1>
          <pre>{JSON.stringify(this.state.data, null, 2)}</pre>
        </header>
      </div>
    );
  }
}

export default App;