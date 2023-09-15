import React, { useState } from "react";

function App() {
  const [selectedFile, setSelectedFile] = useState();
  const [fileContents, setFileContents] = useState();

  const fileSelectedHandler = event => {
    console.log("File selection event triggered");
    setSelectedFile(event.target.files[0]);

    const reader = new FileReader();

    reader.onloadstart = function(event) {
      console.log("File reading started");
    };

    reader.onload = function(event) {
      console.log("File reading completed");
      setFileContents(JSON.parse(event.target.result));
      console.log("File contents set to state");
    };

    reader.onerror = function(event) {
      console.error("Error reading file");
    };

    console.log("Starting to read file");
    reader.readAsText(event.target.files[0]);
  };

  return (
    <div>
      <input type="file" onChange={fileSelectedHandler} />
      {fileContents && <div>{JSON.stringify(fileContents, null, 2)}</div>}
    </div>
  );
}

export default App;