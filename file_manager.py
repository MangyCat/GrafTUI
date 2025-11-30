import os
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Input, Label, DirectoryTree
from textual.screen import ModalScreen

class FileScreen(ModalScreen): # dont move to .tcss
    CSS = """
    FileScreen {
        align: center middle;
        background: rgba(0,0,0,0.7);
    }
    #file_dialog {
        width: 80;
        height: 80%;
        background: #3b4252;
        border: solid #88c0d0;
        padding: 1 2;
        layout: vertical;
    }
    #file_tree {
        height: 1fr;
        background: #2e3440;
        border: solid #4c566a;
        margin-bottom: 1;
    }
    #selected_file {
        margin-bottom: 1;
    }
    
    /* Vertical Button Layout */
    .dialog-btn-container {
        height: auto;
        margin-top: 1;
        layout: vertical;
    }
    
    .dialog-btn-container Button {
        width: 100%;
        margin-top: 1; 
    }
    """

    def __init__(self, title: str = "Select file", initial_path: str = "."):
        super().__init__()
        self.title = title
        self.initial_path = os.path.abspath(initial_path)
        self.selected_path = ""

    def compose(self) -> ComposeResult:
        with Container(id="file_dialog"):
            yield Label(self.title, classes="group-title")
            yield DirectoryTree(self.initial_path, id="file_tree")
            yield Label("Selected path:", classes="group-title")
            yield Input(id="selected_file", placeholder="Filename...")
            # Vertical Stack
            with Container(classes="dialog-btn-container"):
                yield Button("DONE", id="btn_select", classes="btn-primary")
                yield Button("CANCEL", id="btn_cancel", classes="btn-secondary")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:

        self.selected_path = str(event.path)
        self.query_one("#selected_file", Input).value = self.selected_path

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        # Update the selected path when a directory is selected and reflect it in the input
        self.selected_path = str(event.path)
        self.query_one("#selected_file", Input).value = self.selected_path


    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_select":
            path = self.query_one("#selected_file", Input).value
            self.dismiss(path)
        elif event.button.id == "btn_cancel":
            self.dismiss(None)
