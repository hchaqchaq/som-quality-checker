from textual.app import App
from textual.widgets import DataTable
import pandas as pd


class TableApp(App):
    def compose(self):
        yield DataTable()

    def on_mount(self):
        table = self.query_one(DataTable)

        # Example DataFrame
        df = pd.DataFrame({
            "Name": ["Alice", "Bob"],
            "Age": [25, 30],
            "City": ["Paris", "London"]
        })

        # Add columns
        table.add_columns(*df.columns)

        # Add rows
        for row in df.itertuples(index=False):
            table.add_row(*row)


if __name__ == "__main__":
    TableApp().run()