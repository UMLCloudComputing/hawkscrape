import csv
from bs4 import BeautifulSoup
import requests
import io

def getTable(url):

    text_tables = []

    html_content = requests.get(url).text

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all tables with <table>
    tables = soup.find_all('table')

    # Process each table
    for index, table in enumerate(tables):
        # Extract headers
        headers = [header.get_text(strip=True) for header in table.find_all('th')]

        # Extract rows
        rows = []
        for row in table.find_all('tr')[1:]:  # Skip the header row
            cells = row.find_all('td')
            row_data = []
            for cell in cells:
                # Check if the cell contains a list
                ul = cell.find('ul')
                if ul:
                    # Concatenate list items with " and "
                    items = ul.find_all('li')
                    cell_text = ' and '.join(item.get_text(strip=True) for item in items)
                else:
                    cell_text = cell.get_text(separator=' ', strip=True)
                row_data.append(cell_text)
            rows.append(row_data)

        # Create an in-memory string buffer
        csv_buffer = io.StringIO()

        # Write to the string buffer
        csvwriter = csv.writer(csv_buffer)
        csvwriter.writerow(headers)
        csvwriter.writerows(rows)

        # Get the CSV content as a string
        csv_content = csv_buffer.getvalue()
        text_tables.append(csv_content)

        print(csv_content)

    return text_tables

print(getTable('https://www.uml.edu/thesolutioncenter/bill/tuition-fees/undergraduate/undergraduate-ft-2024-2025.aspx'))