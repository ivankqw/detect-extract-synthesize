export const renderBoundingBoxes = (
    pageNumber: number | undefined,
    pages_with_charts_idx: number[] | undefined,
    bboxes: number[][][] | undefined,
    doc_width: number,
    doc_height: number,
    width: number | undefined, // container width
    height: number | undefined // container height
  ) => {
    if (!pageNumber || !bboxes || !pages_with_charts_idx || !width || !height) {
      console.log('renderBoundingBoxes: invalid input', pageNumber, pages_with_charts_idx, bboxes, width, height);
      return null;
    }
    console.log('renderBoundingBoxes', pageNumber, pages_with_charts_idx, bboxes)
  
    const scaleX = width / doc_width;
    const scaleY = height / doc_height;
    const currPage = pageNumber - 1;
    const pageHasChart = pages_with_charts_idx.includes(currPage);
  
    if (!pageHasChart) {
      console.log('No chart on this page', currPage);
      return null;
    }
    // get index of the current page in pages_with_charts_idx
    const pageIndex = pages_with_charts_idx.indexOf(currPage);
  
    return bboxes[pageIndex]
      .filter((box: number[]) => !box.some((coord) => coord === -1)) // Remove invalid boxes
      .map((box: number[], boxIndex) => {
        const scaledBox = {
          x: box[0] * scaleX,
          y: box[1] * scaleY,
          width: (box[2] - box[0]) * scaleX,
          height: (box[3] - box[1]) * scaleY
        };
  
        return (
          <div
            key={`${pageNumber}-${boxIndex}`} // Unique key for each box
            style={{
              border: '2px solid red',
              position: 'absolute',
              left: `${scaledBox.x}px`,
              top: `${scaledBox.y}px`,
              width: `${scaledBox.width}px`,
              height: `${scaledBox.height}px`,
            }}
          />
        );
      });
  };