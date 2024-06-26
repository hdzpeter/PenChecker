import re
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import matplotlib.pyplot as plt
from collections import Counter
import os
import logging

# configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# configuration de la console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_formatter =logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# configuration du logger en mode fichier
file_handler = logging.FileHandler('./logs/ChartMaker.log', mode='w')
file_handler.setLevel(logging.DEBUG)
file_formatter =logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def generate_cve_pie_chart(file_path, output_image_path):
    # Read the markdown file content with the correct encoding
    with open(file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()

    # Improved regex pattern to capture all port, service, and CVE count entries
    pattern = re.compile(r'(\d+): (.*?)(?: version=[\w.]+)? \(CVE Count: (\d+)\)')

    # Extract relevant data from the markdown content
    data = pattern.findall(md_content)

    # Convert the extracted data to a DataFrame
    df = pd.DataFrame(data, columns=['Port', 'Service', 'CVE_Count'])
    df['CVE_Count'] = df['CVE_Count'].astype(int)

    # Filter out entries with 0 CVEs
    df_filtered = df[df['CVE_Count'] > 0]

    # Vérifier s'il y a des CVEs après le filtrage
    if df_filtered.empty:
        logger.info(f"Aucune CVE trouvée pour {file_path}, le graphique ne sera pas créé.")
        return None

    # Summarize service names longer than 2-3 words
    df_filtered['Service'] = df_filtered['Service'].apply(lambda x: ' '.join(x.split()[:3]))

    # Combine port and service name for the labels
    df_filtered['Label'] = df_filtered.apply(lambda row: f"{row['Port']} | {row['Service']}", axis=1)

    # Group by the new label and sum the CVE counts
    df_grouped = df_filtered.groupby('Label').sum().reset_index()

    # Create a pie chart
    plt.figure(figsize=(10, 7))
    plt.pie(df_grouped['CVE_Count'], labels=df_grouped['Label'], autopct='%1.1f%%', startangle=140)
    plt.title('Distribution of CVE Counts by Service')

    # Save the chart as an image (explicitly use png format)
    final_path = os.path.join(output_image_path, 'pie_chart.png')
    plt.savefig(final_path, format='png')
    plt.close()

    logger.info(f"Pie chart saved as {final_path}")
    return final_path

def create_cve_count_by_cvss_chart(md_file_path, output_image_path):
    # Read the markdown file with the correct encoding
    with open(md_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Improved regex pattern to extract CVSS scores
    cvss_scores = re.findall(r"\*\*(\d+\.\d+)\*\*", content)
    if not cvss_scores:
        #print("No CVSS scores found in {md_file_path}. Going on the next one")
        return

    # Convert CVSS scores to floats
    cvss_scores = [round(float(score)) for score in cvss_scores if round(float(score)) > 5]

    # Count the occurrences of each CVSS score
    cvss_count = Counter(cvss_scores)

    # Create a DataFrame for the CVSS score counts
    df_cvss = pd.DataFrame(cvss_count.items(), columns=['CVSS_Score', 'Count'])
    df_cvss = df_cvss.sort_values(by='CVSS_Score')

    # Create a bar chart for CVE counts by CVSS score
    plt.figure(figsize=(12, 6))
    plt.bar(df_cvss['CVSS_Score'].astype(str), df_cvss['Count'], color='skyblue')
    plt.xlabel('CVSS Score')
    plt.ylabel('CVE Count')
    plt.title('CVE Count by CVSS Score')

    # Save the bar chart as an image (explicitly use png format)
    final_path = os.path.join(output_image_path, 'cve_count_by_cvss_chart.png')
    plt.savefig(final_path, format='png')
    plt.close()

    logger.info(f"Bar chart saved as {final_path}")
    return final_path

def import_image(file_path, pie_chart, bar_chart):

    pie_chart = "./" + pie_chart
    bar_chart = "./" + bar_chart

    # Read the original markdown content
    with open(file_path, 'r', encoding='utf-8') as file:
        markdown_content = file.read()

    # Find the position to insert the new content
    insert_index = markdown_content.find("## CVEs")
    if insert_index == -1:
        return "Section 'CVEs' not found in the markdown content."

    # Define the new sections with images
    images_section = f"""
## Répartition des CVEs en fonction des services
![pie_chart]({pie_chart})

## Repartition des CVEs en fonction de leur score CVSS
![bar_chart]({bar_chart})
"""
    # Insert the new sections into the original content
    modified_content = markdown_content[:insert_index] + images_section + markdown_content[insert_index:]

    # Save the modified content back to a new markdown file
    output_file_path = file_path.replace('.md', '_modified.md')
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)

    return output_file_path

def main(file_path, output_image_path):
    pie_chart = generate_cve_pie_chart(file_path, output_image_path)
    bar_chart = create_cve_count_by_cvss_chart(file_path, output_image_path)
    import_image(file_path, pie_chart, bar_chart)

if __name__ == "__main__":
    main()
