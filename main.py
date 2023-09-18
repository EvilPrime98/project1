import requests
from bs4 import BeautifulSoup
import re
import os
import time
from tqdm import tqdm
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar

class WebScraperApp(App):
    def build(self):
        self.layout = GridLayout(cols=1, spacing=10, padding=20)

        self.url_input = TextInput(hint_text='Enter URL', size_hint_y=None, height=50)
        self.layout.add_widget(self.url_input)

        self.start_button = Button(text='Sort', size_hint_y=None, height=50)
        self.start_button.bind(on_press=self.start_scraping)
        self.layout.add_widget(self.start_button)

        self.progress = ProgressBar(max=100, size_hint_y=None, height=30)
        self.layout.add_widget(self.progress)

        self.result_label = Label(text='', size_hint_y=None, height=50, font_size=20)
        self.layout.add_widget(self.result_label)

        return self.layout

    def get_publication_year(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        pattern = re.compile(r'.{0,0}\(Publication\)[^"]*"[^"]*"')
        match = pattern.search(str(soup))

        if match:
            index = match.start()
            date_string = match.string[index-18:index]
            year = re.findall(r'\d{4}', date_string)
            if year:
                return year[0]

        return None

    def start_scraping(self, instance):
        url = self.url_input.text
        if not url:
            self.result_label.text = 'Please enter a valid URL.'
            return

        try:
            response = requests.get(url)
            response.raise_for_status()     
            html = response.text   
            target_string = '<p class="category-page__total-number">'   
            lines = html.split('\n')
            numeric_value = None     
            for i, line in enumerate(lines):
                if target_string in line:
                    match = re.search(r'\d+', lines[i + 1])
                    if match:
                        numeric_value = match.group()
                        break  
        except requests.exceptions.RequestException as e:
            self.result_label.text = "Error al hacer la solicitud HTTP: " + str(e)
            return
        except Exception as e:
            self.result_label.text = "Error: " + str(e)
            return

        if numeric_value is not None:  
            if int(numeric_value) <= 200:

                output_file_path = os.path.join(os.path.expanduser("~"), 'sorted_links.txt')
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                links = []

                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href:
                        links.append(href)

                start_link_index = 0
                for i, link in enumerate(links):
                    if link.endswith("/Gallery"):
                        start_link_index = i
                        break

                start_link_index = start_link_index+1
                end_link_index = links.index("/wiki/Special:Categories")-1
                filtered_links = links[start_link_index:end_link_index+1]
                unique_links = list(set(filtered_links))
                unique_links = [link for link in unique_links if link.startswith('/wiki')]

                for i in range(len(unique_links)):
                    unique_links[i] = "https://dc.fandom.com" + unique_links[i]

                links_with_years = []
                for i, link in enumerate(tqdm(unique_links, desc="Scraping and Processing")):
                    year = self.get_publication_year(link)
                    links_with_years.append((link, year or 'N/A'))
                    # Actualiza el progreso de la barra de progreso
                    self.progress.value = (i + 1) / len(unique_links) * 100

                sorted_links = sorted(links_with_years, key=lambda x: (int(x[1][-4:]) if x[1][-4:].isdigit() else 9999, x[0]))

                with open(output_file_path, 'w', encoding='utf-8') as output_file:
                    output_file.write("Sorted by year of publication:\n")
                    for i, (link, year) in enumerate(sorted_links):
                        link = link.replace("https://dc.fandom.com/wiki/", "")
                        result_line = f"{i+1}. {link} - Publication Year: {year}\n"
                        output_file.write(result_line)

                self.result_label.text = f"Sorting completed. Results saved to {output_file_path}"
            else:
                self.result_label.text = "Too many items to scrape. Limit exceeded (200)."
        else:
            self.result_label.text = "The numeric value was not found or is None."

if __name__ == '__main__':
    WebScraperApp().run()




