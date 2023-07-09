import panthertunes_query
import os

to_delete = [7526959]

for i in to_delete:
    panthertunes_query.delete_post(i)
    #os.mkdir('static/uploads' + '/Proj' + str(i))