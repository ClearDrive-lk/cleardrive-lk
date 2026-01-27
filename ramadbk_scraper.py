from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("https://www.ramadbk.com/japanese-used-toyota-raize-suv_8151499.html")

wait = WebDriverWait(driver, 20)

data = {}

rows = wait.until(
    EC.presence_of_all_elements_located(
        (By.XPATH, "//div[@class='row']//div[strong]")
    )
)

for row in rows:
    try:
        label = row.find_element(By.TAG_NAME, "strong").text.strip()
        value = row.find_element(
            By.XPATH, "following-sibling::div"
        ).text.strip()
        data[label] = value
    except:
        pass

price = wait.until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "span.font_24.font_bold.green_color")
    )
).text

data["FOB Price"] = price

driver.quit()

for k, v in data.items():
    print(f"{k}: {v}")
