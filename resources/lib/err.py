def get_subtitle_language(lang):
    # helper function to map human readable settings to required abbreviation
    languages = {
        0: 'ET',
        1: 'VA',
        2: 'RU'
    }
    return languages.get(int(lang), 'ET')