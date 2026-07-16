import Hero from "./Hero";
import UploadZone from "./UploadZone";
import ExampleQueries from "./ExampleQueries";

export default function Landing({
  dragOver,
  setDragOver,
  onDrop,
  fileRef,
  onFileChange,
  exampleQueries,
}) {
  return (
    <>
      <Hero />

      <UploadZone
        dragOver={dragOver}
        setDragOver={setDragOver}
        onDrop={onDrop}
        fileRef={fileRef}
        onFileChange={onFileChange}
      />

      <ExampleQueries
        queries={exampleQueries}
      />
    </>
  );
}