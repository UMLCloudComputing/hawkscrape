import csv
from bs4 import BeautifulSoup
import requests

html_content = requests.get("https://www.uml.edu/student-services/reslife/housing/housing-food-rates.aspx").text

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

    # Write to CSV
    csv_filename = f'table_{index + 1}.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(headers)
        csvwriter.writerows(rows)

    print(f"CSV file {csv_filename} created successfully.")