#!/usr/bin/env python3
import re
from PySide6.QtCore import QObject, Slot, Property

class MarkdownUtils(QObject):
    """
    Utility class for converting markdown syntax to HTML format
    for use in QML Text elements with textFormat: Text.RichText
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(str, result=str)
    def markdownToHtml(self, text):
        """
        Convert markdown formatting to HTML for display in QML Text elements.
        
        Supported markdown:
        - **bold text** -> <b>bold text</b>
        - *italic text* -> <i>italic text</i>
        - `code` -> <code>code</code>
        - [link text](url) -> <a href="url">link text</a>
        - \n -> <br>
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            Text converted to HTML
        """
        if not text:
            return ""
            
        # Convert line breaks
        html = text.replace('\n', '<br>')
        
        # Bold: **text** -> <b>text</b>
        html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html)
        
        # Italic: *text* -> <i>text</i>
        # Only match *text* that isn't part of **text**
        html = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', html)
        
        # Code: `code` -> <code>code</code>
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        
        # Links: [text](url) -> <a href="url">text</a>
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        
        return html

# For singleton usage in QML
markdown_utils = MarkdownUtils() 