import React, {useState} from "react";
import {JSONTree} from 'react-json-tree';

function App() {
    const [selectedFile, setSelectedFile] = useState();
    const [fileContents, setFileContents] = useState();

    const fileSelectedHandler = event => {
        console.log("File selection event triggered");
        setSelectedFile(event.target.files[0]);

        const reader = new FileReader();

        reader.onloadstart = function (event) {
            console.log("File reading started");
        };

        reader.onload = function (event) {
            console.log("File reading completed");
            try {
                setFileContents(JSON.parse(event.target.result));
                console.log("File contents set to state");
            } catch (error) {
                console.error("Caught error in parsing JSON", error);
            }
            console.log("File contents set to state");
        };

        reader.onerror = function (event) {
            console.error("Error reading file");
        };

        console.log("Starting to read file");
        reader.readAsText(event.target.files[0]);
    };

    return (
        <div>
            <input type="file" onChange={fileSelectedHandler}/>
            {fileContents && <JSONTree data={fileContents}/>}
        </div>
    );
}

export default App;