import csv
from bs4 import BeautifulSoup

html_content = """
<table style="width: 100%" cellspacing="1" cellpadding="1"><colgroup><col style="width: 50%;" span="1" /><col style="width: 25%;" span="1" /><col style="width: 25%;" span="1" /></colgroup><thead><tr><th style="text-align: center;" colspan="3"><strong>Food Plans</strong></th></tr><tr><th style="text-align: left;" align="left">Food Plan Type</th><th style="text-align: left;" align="left">Cost Per Year</th><th style="text-align: left;" align="left">Cost Per Semester</th></tr></thead><tbody><tr><td><strong>Unlimited 400 Plan</strong><br />
This is the default plan for students living in traditional or suite-style buildings. Students living in apartment-style buildings can also upgrade to this unlimited plan. This plan includes unlimited meals and $400 River Hawk dollars per semester.</td><td>$5,920.00</td><td>$2,960.00</td></tr><tr><td><strong>Unlimited 200 Plan</strong><br />
Students living in traditional or suite-style buildings can change to this plan if desired. Students living in apartment-style buildings can upgrade to this unlimited plan. This includes unlimited meals and $200 River Hawk dollars per semester.
<br /></td><td>$5,600.00</td><td>$2,800.00</td></tr><tr><td><strong>Apartment Plan</strong><br />
This is the default plan for all students living in apartment-style buildings unless they select to upgrade to an unlimited 400 or unlimited 200 plan. This plan provides 7 meals a week and $1,000 River Hawk Dollars per semester.
<br /></td><td>$4,630.00</td><td>$2,315.00</td></tr></tbody></table>
"""

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Find the table
table = soup.find('table')

# Extract headers
headers = [header.get_text(strip=True) for header in table.find_all('th')][1:]  # Skip the first header row

# Extract rows
rows = []
for row in table.find_all('tr')[2:]:  # Skip the first two header rows
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
with open('residence_halls.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(headers)
    csvwriter.writerows(rows)

print("CSV file created successfully.")