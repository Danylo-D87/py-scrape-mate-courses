from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
import re  # For regular expressions to extract numbers


@dataclass
class Course:
    """
    Represents a course with its name, short description, duration,
    and optionally the number of modules and topics.
    """
    name: str
    short_description: str
    duration: str
    modules: int | None = None
    topics: int | None = None


def _parse_course_details(card_soup_element: BeautifulSoup) -> Course:

    name_tag = card_soup_element.find(["h2", "h3"])
    name = name_tag.get_text(strip=True) if name_tag else "N/A"

    description_tag = card_soup_element.find("p")
    short_description = (
        description_tag.get_text(strip=True) if description_tag else "N/A"
    )

    duration = "N/A"
    modules = None
    topics = None

    stat_paragraphs = card_soup_element.find_all(
        "p",
        string=re.compile(r"(Тривалість|Модулі|Теми|Duration|Modules|Topics)"),
    )

    for p_tag in stat_paragraphs:

        value_span = p_tag.find_all("span")[-1] \
            if p_tag.find_all("span") else None
        if value_span:
            stat_text = value_span.get_text(strip=True)
            if "Тривалість" in p_tag.get_text():
                duration = stat_text
            elif "Модулі" in p_tag.get_text():
                modules_match = re.search(r"\d+", stat_text)
                if modules_match:
                    modules = int(modules_match.group(0))
            elif "Теми" in p_tag.get_text():
                topics_match = re.search(r"\d+", stat_text)
                if topics_match:
                    topics = int(topics_match.group(0))

    # Fallback for duration if not found in specific stat paragraphs
    if duration == "N/A":
        duration_span = card_soup_element.find(
            "span",
            string=re.compile(r"(\d+\s*(міс|тиж|год|Months|Weeks|Hours))"),
        )
        if duration_span:
            duration = duration_span.get_text(strip=True)

    if duration == "N/A":
        duration_match_anywhere = re.search(
            r"(\d+)\s*(міс|тиж|год|Months|Weeks|Hours)",
            card_soup_element.get_text(),
            re.IGNORECASE,
        )
        if duration_match_anywhere:
            duration = duration_match_anywhere.group(0)

    return Course(
        name=name,
        short_description=short_description,
        duration=duration,
        modules=modules,
        topics=topics,
    )


def get_all_courses() -> list[Course]:
    url = "https://mate.academy"
    courses = []

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Prioritize finding <a> tags that link to /courses/,
        # as they typically represent distinct course cards.
        course_card_elements = soup.find_all(
            "a", href=re.compile(r"^/courses/")
        )

        if not course_card_elements:
            # Fallback if specific links are not found:
            # try to find divs that look like course cards based on content.
            print("No specific course links found. Attempting broader search.")
            course_card_elements = soup.find_all(
                "div",
                lambda tag: tag.name == "div"
                and tag.find("h3")
                and tag.find("p"),
            )
            if not course_card_elements:
                print("No potential course cards "
                      "found by content (h3 and p) either.")

        for card_element in course_card_elements:
            course = _parse_course_details(card_element)
            courses.append(course)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during parsing: {e}")

    return courses


if __name__ == "__main__":
    print("Scraping Mate.Academy courses...")
    all_courses = get_all_courses()
    if all_courses:
        print(f"Found {len(all_courses)} courses: ")
        for course in all_courses:
            print("--- Course ---")
            print(f"Name: {course.name}")
            print(f"Description: {course.short_description}")
            print(f"Duration: {course.duration}")
            if course.modules is not None:
                print(f"Modules: {course.modules}")
            if course.topics is not None:
                print(f"Topics: {course.topics}")
            print("-" * 20)
    else:
        print("No courses found or an error occurred.")
