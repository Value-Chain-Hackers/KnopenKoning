

def get_knowledge_from_wikipedia(search_term):
    import wikipedia
    wikipedia.set_lang("en")
    search_results = wikipedia.search(search_term)
    if not search_results:
        return None
    pages = []
    for result in search_results:
        try:
            page = wikipedia.page(result)
            pages.append(page.content)
        except Exception as e:
            continue
    return pages