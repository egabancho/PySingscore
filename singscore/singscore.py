import matplotlib
import matplotlib.pyplot
import numpy
import pandas
import seaborn
from matplotlib import gridspec, patches

from exception import InvalidNormalisation


def getsignature(path):
    """
    Return the signature as a list od gene id's. If the IDs are digits,
    such as Entrez ID then, ensure that an int is added to the list, for the
    sake of consistency.

    :param path: path to the signature must have no header
    :return: s, a list containing all the genes in the signature
    """
    try:
        sig = open(path, 'rt')
        s = []
        for line in sig.readlines():
            if line.strip().isdigit():
                s.append(int(line.strip()))
            else:
                s.append(line)

        return s

    except OSError as os:
        print('An incorrect input type has been entered for signature '
              'path, please try again. \nDescription: {0}'.format(os))

    except TypeError as te:
        print('Incorrect data type, please enter the correct signature path. \n'
              'Description: {0}'.format(te))

def normalisation(norm_method, score_list, score, library_len, sig_len,
                  mad = True):

    """

    :param norm_method: method of normalisation, standard or theoretical
    :param score_list: list of scores will each be normalised
    :param score: average score (average of list)
    :param library_len: length of the library (int)
    :param sig_len: length of the signature used to generate the scores

    :return: a tuple, containing the normalised score (float) and an array of
    each genes score normalised
    """
    try:
        if norm_method == 'standard':
            norm = score / library_len
            if mad:
                u = numpy.array(score_list) / library_len
        elif norm_method == 'theoretical':
            low_bound = (library_len + 1) / 2
            upper_bound = library_len - ((sig_len - 1) / 2)
            norm = (score - low_bound) / (upper_bound - low_bound)
            if mad:
                u = ((numpy.array(score_list)) - low_bound) / (upper_bound - low_bound)
        if mad:
            return norm, u
        elif mad == False:
            return norm

        raise InvalidNormalisation

    except:
        print('Normalisation method must be standard or theoretical.')

def normalisation_rank(norm_method, ranks, library_len, sig_len):

    """

    :param norm_method: method of normalisation, standard or theoretical
    :param ranks: a dataframe of ranks
    :param library_len: length of library (int)
    :param sig_len: length of the signature used to generate the dataframe

    :return: a dataframe with normalised ranks for each gene in each sample
    """
    try:
        if norm_method == 'standard':
            ranks = ranks/library_len
        elif norm_method == 'theoretical':
            low_bound = (library_len+1)/2
            upper_bound = library_len - ((sig_len-1)/2)
            ranks = (ranks- low_bound)/(upper_bound-low_bound)

        raise InvalidNormalisation

        return ranks
    except InvalidNormalisation:
        print('Normalisation method must be standard or theoretical.')


def score(up_gene, sample, down_gene = False, norm_method = 'standard',
          norm_down = 0, full_data= False):
    """
    This function will generate a score, using singscore method for each
    sample in a cohort. It may be used for either single direction signatures
    or both up and down.
    Gene identifiers used in signature must be the same as those used in the
    sample for example both Entrez or GeneSymbol

    :param up_gene: can be either a path to a .txt file containing genes
    (if so there must be no header) OR a list of genes
    :param sample: a dataframe, with row index as gene id (must be the same
    as the the gene identifier in the signature)
    :param down_gene: can be either a path to a .txt file containing genes
    (if so there must be no header) OR a list of genes. Default in False,
    for use in single direction signatures
    :param norm_method: choose a normalisation method. Default is
    'standard', where score is simply divided by the library size. This is
    acceptable for most case. Theoretcial uses the theoretical minimum and
    maximum to normalise the score.
    :param norm_down: if down_gene is False, then this is the value used to
    calculate the total score (0)
    :param full_data: if True then a dataframe with scores (both up and
    down if down_gene != False) and dispersion
    will be returned, otherwise just the scores will be returned

    :return: a dataframe of scores with or without dispersion
    """

    data = pandas.DataFrame()

    # if up_gene and/or down_gene are a path to txt file then gene_path =
    # True and use getsignature function to open and generate a list of
    # genes
    if type(up_gene) is str:
        up_gene = getsignature(up_gene)
        if down_gene != False:
            down_gene = getsignature(down_gene)

    for i in sample.columns:
        # rank the genes -> Ties will be taken as the rank of the first
        # appearance
        up_sort = sample[i].rank(method='min', ascending=True)
        # su is a list to contain the score for each gene in the gene list
        su = []

        # for every gene in the list gene get the value at that
        # index/rowname (the gene) and the sample that is equal to i
        for j in up_gene:
            if j in up_sort.index:
                su.append(up_sort.get_value(j, i))
        # normalise the score for the number of genes in the signature
        score_up = numpy.mean(su)

        # normalisation
        norm_up = normalisation(norm_method= norm_method, library_len=len(
            sample.index), score_list=su, score = score_up, sig_len=len(up_gene))
        u = norm_up[1]
        norm_up = norm_up[0]

        # find dispersion
        median_up = numpy.median(u)
        mad_up = numpy.median(abs(u-median_up))


        # ==== repeat with down genes,flipping the data frame around
        if down_gene != False:
            # this is the standard for scoring, opposite to up
            down_sort = sample[i].rank(method='min', ascending=False)

            # sd is a list to contain the score for each gene in the
            # gene list
            sd = []
            # for every gene in the list gene get the value at that
            # index/rowname (the gene) and the sample that is equal to i
            for k in down_gene:
                if k in sample.index:
                    sd.append(down_sort.get_value(k,i))

            score_down = numpy.mean(sd)

            # normalisation
            norm_down = normalisation(norm_method=norm_method, library_len=len(
                sample.index), score_list=sd, score=score_down, sig_len=len(
                down_gene))
            d = norm_down[1]
            norm_down= norm_down[0]
            # find dispersion
            median_down = numpy.median(d)
            mad_down = numpy.median(abs(d-median_down))

        total_score = norm_up + norm_down
        # make the score dataframe
        if full_data == True and down_gene != False: # if all data is
            # wanted and there is a down gene list
            temp_df = pandas.DataFrame({'up_score': norm_up,
                                    'mad_up':mad_up,'down_score':norm_down,
                                    'mad_down':mad_down,
                                    'total_score': total_score,
                                    'total_mad':mad_down + mad_up},
                                   index=[i])
            temp_df = temp_df[['up_score', 'mad_up', 'down_score',
                               'mad_down', 'total_score', 'total_mad']]
        elif full_data == True and down_gene == False: # if all data is
            # wanted and there is only up gene list
            temp_df = pandas.DataFrame({'total_score': total_score,
                                        'total_mad': mad_up,
                                        },index=[i])
        else: # default, regardless of down gene list, just make total
            # score
            temp_df = pandas.DataFrame({'total_score':total_score},
                                       index=[i])

        if len(data.columns) == 0:
            data = temp_df

        else:
            data = data.append(temp_df)


    return data

def rank(up_gene, sample, down_gene = False,norm_method = 'standard'):

    """
    This function will generate a dataframe of ranks, using singscore method
    for each gene in each sample in a cohort. It may be used for either single
    direction signatures or both up and down. The difference between rank
    and score is that the rank simply shows where in the library the genes
    of a signature are placed high normalised rank means that the gene is
    highly expressed, whereas a low rank means the gene is lowly expressed.

    Gene identifiers used in signature must be the same as those used in the
    sample for example both Entrez or GeneSymbol

    :param up_gene: can be either a path to a .txt file containing genes
    (if so there must be no header) OR a list of genes
    :param sample: a dataframe, with row index as gene id (must be the same
    as the the gene identifier in the signature)
    :param down_gene: can be either a path to a .txt file containing genes
    (if so there must be no header) OR a list of genes. Default in False,
    for use in single direction signatures
    :param norm_method: choose a normalisation method. Default is
    'standard', where score is simply divided by the library size. This is
    acceptable for most case. Theoretcial uses the theoretical minimum and
    maximum to normalise the score.

    :return: a dataframe which has normalised ranks for each gene in a
    signature for each sample in a cohort.
    """

    # ============ get up and down signatures ===============
    # if up_gene and/or down_gene are a path to txt file then gene_path =
    # True and use getsignature function to open and generate a list of
    # genes

    if type(up_gene) is str:
        up_gene = getsignature(up_gene)
        if down_gene != False:
            down_gene = getsignature(down_gene)
    su = {}
    sd = {}
    for i in sample.columns:
        # rank the genes -> Ties will be taken as the rank of the first
        # appearance
        up_sort = sample[i].rank(method='min', ascending=True)
        # su is a dictionary to contain the gene id, rank

        su[i] = []
        # for every gene in the list gene get the value at that
        # index/rowname (the gene) and the sample that is equal to i
        for j in up_gene:
            if j in up_sort.index:
                su[i].append((j, up_sort.get_value(j,i)))


        # ==== repeat with down genes
        if down_gene != False:
            # for ranking use the same direction as up
            down_sort = sample[i].rank(method='min', ascending=True)

            # sd is a dictionary to contain the score for each gene in the
            # gene list

            sd[i] = []
            # for every gene in the list gene get the value at that
            # index/rowname (the gene) and the sample that is equal to i
            for k in down_gene:
                if k in sample.index:
                    sd[i].append((k, down_sort.get_value(k,i)))

    # dataframes of ranks for each gene in each sample and then normalise
    # ranks (0 to 1, based on library size) standard = simply divide by the
    # library size theoretical = use the theoretical minimum and maximum for
    up_ranks = pandas.DataFrame({s: pandas.Series({g: r for g,r in su[s]}) for
                                s in su})
    up_ranks = normalisation_rank(norm_method= norm_method, ranks=up_ranks,
                                  library_len=len(sample.index),
                                  sig_len=len(up_gene))

    if down_gene != False:
        down_ranks = pandas.DataFrame({s: pandas.Series({g: r for g,r in sd[s]})
                                       for s in sd})

        down_ranks = normalisation_rank(norm_method=norm_method,
                                        ranks=down_ranks,
                                      library_len=len(sample.index),
                                      sig_len=len(down_gene))

        down_ranks['up_or_down'] = 'down'
        up_ranks['up_or_down'] = 'up'

    if down_gene != False:
        ranks = up_ranks.append(down_ranks)
    else:
        ranks = up_ranks

    return (ranks)


def definegrid(nrows , ncols ):

    """
    Define a grid for the placement of graphs
    :param nrows: number of rows int
    :param ncols: number of columns int
    :return: a tuple containing the grid in [0] and a list of tuples
            correpsponding to the grid positions for placement of individual
            plots.
    """
    grid_outer = gridspec.GridSpec(nrows=nrows, ncols=ncols)

    grid_outer.update(left=0.1, right=0.95, wspace=0.4, hspace=0.6,
                      bottom=0.1, top=0.93)

    ax_list = [(i,j) for i in range(nrows) for j in range(ncols)]

    return grid_outer,ax_list



def plotrankdist(ranks, nrows= 1, ncols = 1, counter = 0, t = False, colour_1 =
                'black', colour_2 = 'grey', singledir = True, output =
                 False, show= True):

    """
    Takes the dataframe output of rank and will saves figure to output path
    (if supplied) and optionally shows figure. Must supply nrows and ncols
    that are sutiable for the number of plots to generated

    :param ranks: a dataframe output of rank, if up and down regulated
                genes, must have a column called 'up_or_down' annotating the
                genes in each group.
    :param nrows: predefined number of rows, default 1 for single figure
    :param ncols: predefined number of cols, default 1 for single figure
    :param counter: counter for placement of plot in grid
    :param t: for title, default False not supplied use column titles
    :param colour_1: colour for up-regulated or single direction gene
                    signature, default black
    :param colour_2: colour for down-regulated genes, default grey
    :param singledir: default is False for single direction signature. May
                    be supplied as True for bi-directional, but will be changed
                    to True if 'up_or_down' column present.
    :param output: output path for optional saving of figure
    :param show: show figure

    :return: matplotlib.figure.Figure
    """
    # set the style of the graphs to have no background or spines
    seaborn.set_style('ticks')

    # define the grid set up for the plots
    grid = definegrid(nrows=nrows, ncols = ncols)
    grid_outer = grid[0]
    ax_list = grid[1]

    fig = matplotlib.pyplot.figure(figsize=(20, 10))

    # if the signature contains up and down regulated genes,
    # then 'up_or_down' column should be included as annotation. This is
    # standard output of rank for bi-directional signatures.
    if 'up_or_down' in ranks.columns:
        # select up and down genes and put in separate dataframes
        ranks_down = ranks[ranks['up_or_down'] == 'down']
        ranks = ranks[ranks['up_or_down'] == 'up']
        # remove the 'up_or_down' column
        ranks = ranks.drop(labels = ['up_or_down'], axis = 1)
        ranks_down = ranks_down.drop(labels = ['up_or_down'], axis = 1)
        # set singledir to False, for the addition of the down-regulated set
        #  the plots
        singledir = False

    # plot each column supplied separately
    for r in range(len(ranks.columns)):
        # get the column name, for matching with down if required and
        # setting as title if necessary
        sample = ranks.columns[r]
        # set title
        if t == False:
            title = sample
        else:
            title = t
        # if single direction, then the plot will have two panels
        if singledir:
            inner = gridspec.GridSpecFromSubplotSpec(nrows=2, ncols=1,
                                                 subplot_spec=
                                                 grid_outer[ax_list[counter]])
        # if up and down direction, then the plot will have three panels
        else:
            inner = gridspec.GridSpecFromSubplotSpec(nrows=3, ncols=1,
                                                     subplot_spec=
                                                     grid_outer[
                                                         ax_list[counter]])
            # add the bottom axis for down-regulated barcode plot
            ax3 = fig.add_subplot(inner[2,0])

        # density plot
        ax1 = fig.add_subplot(inner[0, 0])
        # up-regulated barcode plot
        ax2 = fig.add_subplot(inner[1, 0])

        # plot the density
        seaborn.distplot(ranks[sample], hist=False, rug=False,
                         color=colour_1,
                         ax=ax1,
                         kde=True, label='up-regulated genes')
        if singledir == False:
            seaborn.distplot(ranks_down[sample], hist=False, rug=False,
                             color=colour_2,
                             ax=ax1,
                             kde=True, label='down-regulated genes')
        else:
            ax1.xaxis.label.set_visible(False)
        matplotlib.pyplot.xlim(0, 1)
        ax1.set_xticklabels([])
        ax1.set_xlim(-.1, 1.1)
        ax1.tick_params(axis='both', which='both', length=0)
        matplotlib.pyplot.xlim(-.1, 1.1)

        # plot the barcodes
        seaborn.distplot(ranks[sample], hist=False, rug=True,
                         color=colour_1,
                         ax=ax2,
                         kde=False, rug_kws={'height': 0.5})
        matplotlib.pyplot.xlim(0, 1)
        ax2.set_xticklabels([])
        ax2.set_yticklabels([])
        ax2.set_xlim(-.1, 1.1)
        ax2.tick_params(axis='both', which='both', length=0)
        ax2.xaxis.label.set_visible(False)
        matplotlib.pyplot.xlim(0, 1)
        ax1.set_title(title)
        if singledir:
            # if single direction then label ranks on bottom axis
            ax2.set_xlabel('Ranks', fontsize=12)
        else:
            # add down barcode and label as ranks
            seaborn.distplot(ranks_down[sample], hist=False, rug=True,
                             color=colour_2,
                             ax=ax3,
                             kde=False, rug_kws={'height': 0.5})
            ax3.set_xticklabels([])
            ax3.set_yticklabels([])
            ax3.set_xlabel('Ranks', fontsize=12)

        seaborn.despine()
        # update counter to move to the next panel
        counter = counter + 1
    if output:
        matplotlib.pyplot.savefig(output)
    if show:
        matplotlib.pyplot.show()

    return fig

def plotdispersion(score, nrows = 1, ncols = 1, counter = 0, ctrlstring =
                    False, teststring= False, testlabel = False, colour_1 =
                    'grey', colour_2 = 'black', outpath = False, show = True):
    """
    Takes a dataframe, the output of score(), with full_data set to True. It
    will plot the MAD of up, down and total scores if supplied or just the
    MAD of total score

    :param score:   a dataframe of scores, containing MAD values, the output
                    of score, with full_data set to True
    :param nrows:   default 1, can be set if plotdispersion is in a loop for
                    plotting multiple sample sets
    :param ncols:   default 1, can be set if plotdispersion is in a loop for
                    plotting multiple sample sets
    :param counter: default 0, can be set if plotdispersion is in a loop for
                    plotting multiple sample sets
    :param ctrlstring: a string which may be found in all control samples,
                        for use if visualising pairs of groups is important
    :param teststring: a string which may be found in all test samples,
                        for use if visualising pairs of groups is important
    :param testlabel: a string which may be given to all test samples (not
                        controls)
    :param colour_1: default grey
    :param colour_2: default black
    :param outpath: optional outpath if saving is needed
    :param show: optional show, default True

    :return: matplotlib.figure.Figure
    """


    # set the style of the graphs to have no background or spines
    seaborn.set_style('ticks')

    # define the grid set up for the plots
    grid = definegrid(nrows=nrows, ncols=ncols)
    grid_outer = grid[0]
    ax_list = grid[1]



    # check if mad is present
    if 'total_mad' in score.columns:
        # if differential colors for conditions is required, define the
        # groups, colors and generate patch for legend, otherwise default to
        #  no colors or legend
        if ctrlstring:
            score['cond'] = numpy.where(score.index.str.contains(
                ctrlstring), ctrlstring, testlabel)
            score['color'] = numpy.where(score['cond'] == ctrlstring,
                                         colour_1, colour_2)
            ctrl = matplotlib.patches.Patch( color = colour_1, label = ctrlstring)
            test = matplotlib.patches.Patch(color=colour_2, label = testlabel)
        else:
            score['cond'] = ' '
            score['color'] = colour_1
        # if up, down and total are required, define inner grid as a 1 x 3
        # and fig size to 10h x 30w and place up, down and total axes
        if 'down_score' in score.columns:
            fig = matplotlib.pyplot.figure(figsize=(30, 10))
            inner = gridspec.GridSpecFromSubplotSpec(nrows=1, ncols=3,
                                                 subplot_spec=
                                                 grid_outer[ax_list[counter]])
            up_inner = fig.add_subplot(inner[0,0])
            down_inner = fig.add_subplot(inner[0,1])
            total_inner = fig.add_subplot(inner[0,2])
            # for each group of x,y,lab and color plot a point on a scatter
            for x,y,lab,col in zip(score['up_score'], score['mad_up'],
                                   score['cond'], score['color']):
                up_inner.scatter(x,y,label = lab, color=col)


            for x,y,lab,col in zip(score['down_score'], score['mad_down'],
                                   score['cond'], score['color']):
                down_inner.scatter(x,y,label = lab, color=col)
            up_inner.set_xlabel('Up score')
            up_inner.set_ylabel('MAD (Up score)')
            down_inner.set_xlabel('Down score')
            down_inner.set_ylabel('MAD (Down score)')

        # if only total is required, fig size is 10 x 10 and 1 x 1 grid
        else:
            fig = matplotlib.pyplot.figure(figsize=(10, 10))
            inner = gridspec.GridSpecFromSubplotSpec(nrows=1, ncols=1,
                                                     subplot_spec=
                                                     grid_outer[
                                                         ax_list[counter]])
            total_inner = fig.add_subplot(inner[0, 0])

        for x,y,lab,col in zip(score['total_score'], score['total_mad'],
                               score['cond'], score['color']):
            total_inner.scatter(x,y,label = lab, color=col)
        total_inner.set_xlabel('Total score')
        total_inner.set_ylabel('MAD (Total score)')
        # if differential colors plot legend
        if ctrlstring:
            total_inner.legend(handles=[ctrl, test])
        seaborn.despine()
        if outpath:
            matplotlib.pyplot.savefig(outpath)
        if show:
            matplotlib.pyplot.show()

        return fig
    else:
        print('No dispersion values present, please re-run score with '
              'full_data = True')


def permutate(sample, n_up, n_down = False, reps= 100, norm_method =
            'standard', rs_down = 0):

        """
        Bootstrap a random population of scores for a given sample, that is
        dependent on a the number of genes in a signature. Take a sample and
        score it with randomly selected genes from a gene list. Returns a
        dataframe the length of the permutations (reps) desired with each
        column corresponding to a sample. It should be noted

        :param sample:  sample is a dataframe containing the expression data
                        from at least one sample (more may be used).
        :param n_up:    the number of genes in the up gene signature
        :param n_down:  the number of gens in the down signature, may be false
        :param reps:    the number of permutations, default is 10000
        :param norm_method: the normalisation method, should be the same as
                            the one used to score the sample with the actual
                            signature. Default is standard
        :param rs_down:     default 0, if n_down is 0, then this is the default
                            down score, used to calculate total score
        :return:    a dataframe containing the permutated scores, each column
                    is a sample.
        """
        # set seed
        numpy.random.seed(555)
        # dataframe for permutated scores
        null = pandas.DataFrame()

        for s in sample.columns:
            scores = [] # empty list to append scores to
            # for efficiency sort the sample once
            up_sort = sample[s].rank(method = 'min', ascending = True)
            if n_down:
                down_sort = sample[s].rank(method = 'min', ascending = False)

            # permutate
            for r in range(reps):
                # select n_up genes at random
                up_gene = numpy.random.choice(sample.index, n_up,
                                              replace=False)
                ru = [] # empty list to append up score to
                # find the rank of the genes
                for ug in up_gene:
                    if ug in up_sort.index:
                        ru.append(up_sort.get_value(ug,s))
                # calculate the mean of ranks
                rs_up = numpy.mean(ru)
                # normalise
                rs_up = normalisation(norm_method = norm_method,
                                      score_list=ru, score = rs_up,
                                      mad=False, library_len=len(
                        sample.index), sig_len= n_up)

                if n_down:
                    # select n_down genes
                    down_gene = numpy.random.choice(sample.index, n_down,
                                                    replace=False)
                    rd = [] # an empty list to append down scores to
                    # find the rank of genes
                    for dg in down_gene:
                        if dg in down_sort.index:
                            rd.append(down_sort.get_value(dg, s))
                    # find the mean down rank
                    rs_down = numpy.mean(rd)
                    # normalise
                    rs_down = normalisation(norm_method=norm_method, score =
                                            rs_down, score_list=rd, mad=False,
                                            library_len=len(sample.index),
                                            sig_len=n_down)
                #   calculate the random score and append to scores list
                rs = rs_down + rs_up
                scores.append(rs)

            # null column = sample = scores
            null[s] = scores
        return null

def empiricalpval(permutations, score):

    """
    The empirical p value is the probability of observing a score greater
    than observed based on the permutation of the sample.

    p = (r + 1)/(m + 1), where r is the number of scores in the permutated
    data that is greater than the actual score and m is the number of
    permutations

    :param permutations: the dataframe outputted from permutations function
    :param score:   the score calculated from the actual signature in the
                    samples in the permutations dataframe
    :return: a dataframe of empirical p values, each row representing a sample
    """
    # dictionary for p values
    emp_p = {}

    for sample in permutations.columns:
        # check if the sample is the same as the row in score
        if sample in score.index:
            # extract the score
            s = score.get_value(sample, 'total_score')
            # calculate r = number of permutated scores greater than the
            # actual score
            r = len(permutations[permutations[sample]>s]) + 1
            # m = the number of permutations
            m = len(permutations[sample]) + 1
            p = r/m
            # add an entry to the p dictionary sample:pvalue
            emp_p[sample] = p
    # create a data frame of p values
    emp = pandas.DataFrame.from_dict(data=emp_p, orient='index')
    emp = emp.rename(columns={0:'empirical p value'})

    return emp

def nulldistribution(permutations, score,  nrows = 1, ncols = 1,
                     counter = 0, outpath = False, show = True, color =
                     'grey', threshold = False):

    """
    Generate histogram/density plot of permutated data, with actual score
    indicated by a vertical line (blue) and a significance threshold
    indicated by red vertical line

    :param permutations:    a dataframe of permutated scores, output from the
                            permutations function
    :param score: a dataframe of scores for the samples
    :param nrows:   number of rows for graph grid, if single sample,
                    nrows should be 1
    :param ncols:   number of cols for graph grid, if single sample,
                    ncols should be 1
    :param counter: the initial placement of the graph in the grid
    :param outpath: if the figure is to be saved, the outpath
    :param show: show the graph, defualt True
    :param color: colour for the graph, default grey
    :param threshold: a significance threshold to mark on the graph
    :return: matplotlib.figure.Figure
    """

    # set the style of the graphs to have no background or spines
    seaborn.set_style('ticks')

    # define the grid set up for the plots
    grid = definegrid(nrows=nrows, ncols=ncols)
    grid_outer = grid[0]
    ax_list = grid[1]
    # set figure size
    fig = matplotlib.pyplot.figure(figsize=(10 * ncols, 10 * nrows))

    for p in permutations:

        # set the placement of the graph
        inner = gridspec.GridSpecFromSubplotSpec(nrows=1, ncols=1,
                                             subplot_spec=
                                             grid_outer[ax_list[counter]])
        counter = counter + 1
        ax = fig.add_subplot(inner[0, 0])
        # distribution plot
        seaborn.distplot(permutations[p],hist=True, kde_kws={'color':color},
                         label='null distribution',ax=ax, hist_kws={
                'color':color})
        ax.set_xlabel('Score')
        ax.set_ylabel('Density')
        ax.axvline(score.get_value(p,'total_score'), color = 'b')
        # if threshold is true then calculate what the 0.05 ie 95th percentile
        if threshold:
            t = numpy.percentile(permutations[p], ((1-threshold)*100))
            ax.axvline(x = t, color = 'r', linestyle = 'dashed' )
        ax.set_title(p)
        seaborn.despine()

    if outpath:
        matplotlib.pyplot.savefig(outpath)
    if show:
        matplotlib.pyplot.show()

    return fig


