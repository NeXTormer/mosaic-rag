from mosaicrs.MosaicRS import MosaicRS

rs = MosaicRS()


InitialSearch (MOSAIC)
rs.Rerank()
rs.Summarize(20)


InitialSearch (MOSAIC)
rs.conversationalQuery("what is ..")



docs = pd.read(test.csv)
rs.conversationalQuery("what is ..")


pipe = pipe([Initialsearch(), Reranker(), conversationalsearch(*)])
pipe.search('asdfdsf')






rs.addModifier()

response = rs.search(query='werner', method='llm-ranked', type='json')
