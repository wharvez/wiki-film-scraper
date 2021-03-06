from detail import Detail
from work import Work
from helpers import regexes, info
from helpers.general import *


class Film:
    def __init__(self) -> None:
        self.titles = []
        self.cast = []


    def set_titles(self, **kwargs):
        summary_title = kwargs.get('summary_title')
        alts = kwargs.get('alts')
        page_title = kwargs.get('page_title')
        titles = []
        if page_title.endswith(' - Wikipedia'):
            page_title = page_title[:-12]
        self.titles.append(Detail(raw_detail=page_title, note='page'))
        if summary_title:
            for title in [summary_title] + alts:
                titles.append(remove_enclosures(remove_footnotes(title).strip(), ['"', '"']))
            self.titles.append(Detail(detail=titles[0], note='summary'))
            if len(titles) > 1:
                for alt_title in titles[1:]:
                    self.titles.append(Detail(detail=alt_title, note='alt'))


    def set_cast_ul(self, **kwargs):
        first_ul = kwargs.get('first_ul')
        uls = []
        ul_parent = first_ul.parent
        if ul_parent.name == 'td':  # Test case: Caged
            uls.extend(first_ul.find_previous('tr').find_all('ul'))
        else:
            uls.append(first_ul)
        for ul in uls:
            lis = ul.find_all('li', recursive=False)
            # The recursive=False option prevents nested lis from getting their own item in the list, which would be duplicative due to their inclusion in the text of their parent (see note below)
            for li in lis:
                li_class = li.attrs.get('class')
                if li_class and li_class[0] == 'mw-empty-elt':  # Test case: The Chase
                    continue
                li_text = remove_footnotes(li.text.strip())
                if '\n' in li_text:  # Test case: The Lady from Shanghai
                    li_text = li_text.replace('\n', ' (').strip() + ')'
                    # When accessing the text property of an li tag that includes a nested list, Beautiful Soup appends the text of its child lis to it, separating them with \n. The operation above should enclose the text of a nested li in parens, which will then be converted into a note.
                name, role = split_actor(li_text, li.find('a'))
                actor_detail = Detail(raw_detail=name, raw_role=role)
                actor_detail.remove_year_notes()
                self.cast.append(actor_detail)


    def set_cast_table(self, **kwargs):  # Test case: Pushover
        cast_table = kwargs.get('cast_table')
        cast_wtables = cast_table.find_all('table', class_='wikitable')
        for wtable in cast_wtables:
            wtable_rows = wtable.find_all('tr')
            for row in wtable_rows:
                row_tds = row.find_all('td')
                if not row_tds:
                    continue
                tds_clean = []
                for td in row_tds:
                    td_italic = td.find('i')
                    if td_italic and td_italic.text != td.text:
                        td_italic.decompose()  # To eliminate extraneous words such as "with" and "introducing," which appear in italics in the Pushover cast table
                    td_text = remove_footnotes(td.text.replace('\n', '').strip())
                    tds_clean.append(td_text)
                name, role = tds_clean[:2]
                actor_detail = Detail(raw_detail=name, raw_role=role)
                actor_detail.remove_year_notes()
                self.cast.append(actor_detail)


    def set_infobox_details(self, **kwargs):
        mapping_table = kwargs.get('mapping_table')
        if not mapping_table or type(mapping_table) is not dict:
            mapping_table = info.labels_mapping_table
        if mapping_table and type(mapping_table) is not dict:
            warn('Parameter "mapping_table" must be of type dict. Reverted to default.')
        infobox = kwargs.get('infobox')
        label_tags = infobox.find_all('th', class_='infobox-label')
        if not label_tags:
            warn(f'No label tags found in infobox for {self.titles[0].detail}.')
            return
        for label_tag in label_tags:
            label = label_tag.text.strip()
            if label not in [*mapping_table]:
                continue
            label = mapping_table[label]
            details_tag = label_tag.find_next('td')
            lines = get_details_lines(details_tag)
            spread_notes(lines)  # In case a note followed by a colon precedes several details to which it should be applied. Test case: The Lady from Shanghai
            join_parens(lines)  # In case a parenthetical note and its parentheses get split up across multiple lines, which happens when the note is a link.
            details = []
            for line in lines:
                print_param = False
                if label == 'distribution':
                    print_param = True
                detail = Detail(raw_detail=line, print_param=print_param)
                if label in info.special_methods:
                    getattr(detail, info.special_methods[label])()
                details.append(detail)
            existing_details = getattr(self, label, None)
            if existing_details:
                existing_details.extend(detail for detail in details if detail not in existing_details)
            else:
                setattr(self, label, details)
    

    def set_basis(self, **kwargs):
        basis_tag = kwargs.get('basis_tag')
        writing = getattr(self, 'writing', None)
        if basis_tag:
            work = Work(basis_tag, self.titles[0].detail)
            work.format_and_creators(writing)
            self.basis = work
        elif writing:  # Test case: La Nuit du Carrefour
            creators = list(filter(lambda writer: any(note in info.work_format_words for note in writer.notes), writing))
            if creators:
                work_kwargs = dict(
                    creators = [creator.detail for creator in creators],
                    works = [self.titles[0].detail],
                    film_title = [self.titles[0].detail],
                    formats = [note for creator in creators for note in creator.notes if note in info.work_format_words]
                    )
                self.basis = Work(**work_kwargs)
