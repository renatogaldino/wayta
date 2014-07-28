# coding: utf-8

INDEXES_DOC_TYPE = {
    'institutions': 'institution',
    'countries': 'country',
}


class DataBroker(object):

    def __init__(self, es):
        self.es = es

    def _parse_data(self, data, q):

        response = {
            'head': {
                'match': None,
            },
            'choices': []
        }

        if len(data['hits']['hits']) == 0:
            response['head']['match'] = False
            return response

        if data['hits']['hits'][0]['_source']['form'].lower() == q.lower():
            response['head']['match'] = 'exact'
            response['choices'].append(
                {
                    'value': data['hits']['hits'][0]['_source']['name'],
                    'score': data['hits']['hits'][0]['_score'],
                }
            )
            return response

        choices = {}
        for hit in data['hits']['hits']:

            choices.setdefault(hit['_source']['name'], {'country': hit['_source']['country'], 'score': float(hit['_score'])})

        ch = []
        for choice, values in choices.items():
            ch.append({'value': choice, 'country': values['country'], 'score': values['score']})

        response['choices'] = sorted(ch, key=lambda k: k['score'], reverse=True)

        if len(response['choices']) == 1:
            response['head']['match'] = 'by_similarity'
        else:
            response['head']['match'] = 'multiple'

        return response

    def similar(self, index, q):

        if not index in INDEXES_DOC_TYPE:
            raise TypeError('Invalid index name: %s' % index)

        data = {}

        if q:
            data['form'] = q

        qbody = {
            'query': {
                'fuzzy_like_this_field': {
                    'form': {
                        'like_text': q,
                        'fuzziness': 2,
                        'max_query_terms': 100
                    }
                }
            }
        }

        return self._parse_data(
            self.es.search(
                index=index,
                doc_type=INDEXES_DOC_TYPE[index],
                body=qbody
            ),
            q
        )
