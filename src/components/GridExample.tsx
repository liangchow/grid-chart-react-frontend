import { useState } from "react";
import { checkboxColumn, DataSheetGrid, floatColumn, keyColumn, textColumn, type Column } from "react-datasheet-grid";
import 'react-datasheet-grid/dist/style.css'

// define types
interface Row {
    make: string;
    model: string;
    price: number;
    electric: boolean;
}

function GridExample() {
  const [data, setData] = useState<Row[]>([
    { make: "Tesla", model: "Model Y", price: 64950, electric: true },
    { make: "Ford", model: "F-Series", price: 33850, electric: false },
    { make: "Toyota", model: "Corolla", price: 29600, electric: false },
  ]);

  const columns: Column<Row>[] = [
    { ...keyColumn<Row, 'make'>('make', textColumn), title: "Make"},
    { ...keyColumn<Row, 'model'>('model', textColumn), title: "Model"},
    { ...keyColumn<Row, 'price'>('price', floatColumn), title: "Price"},
    { ...keyColumn<Row, 'electric'>('electric', checkboxColumn), title: "Electric"},
  ];

  return (
    <div style={{ height: 500 }}>
        <DataSheetGrid<Row> value={data} columns={columns} onChange={setData} />
    </div>
  );
};

export default GridExample
