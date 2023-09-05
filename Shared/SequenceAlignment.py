"""
    This program aligns two given sequences.
    The algorithm used is Needleman-Wunsch algorithm.
    Details of the algorithm:
    - Original Algorithm:
        A general method applicable to the search for similarities in the amino acid
        sequence of two proteins
        https://www.sciencedirect.com/science/article/pii/0022283670900574?via%3Dihub
    - Other references:
        Application of Needleman-Wunch Algorithm to identify mutation in DNA sequences
        of Corona virus
        https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7106772/

    Author: Terrence Lim.
"""

SCORES = {
        "MATCH": 10,
        "MISMATCH": -10,
        "INDEL": -1
}

MISSING = -1

def SequenceAlignment(S1: list, S2: list):
    """This function aligns elements in S1 to the elements in S2.

    args:
        S1 (list): first sequence.
        S2 (list): second sequence.

    returns:
        (dict) dict of paired aligned element ids.
    """
    
    # NeedlemanWunsch algorithm computes from back to front.
    # Thus, we first reverse both sequences.
    S1.reverse()
    S2.reverse()
    
    Matrix = NeedlemanWunsch(S2, S1)
    reversedOrderAlignedElemIds = ComputeAlignment(Matrix, S1, S2)

    # Reverse the aligned node ids to the correct order, i.e., order of generation.
    correctOrderAlignedElemIds = reverseAlignedOrder(reversedOrderAlignedElemIds)

    return correctOrderAlignedElemIds

def NeedlemanWunsch(seq_1: list, seq_2: list):
    """This function runs Needleman-Wunsch algoithm to populate
    the matrix with the scores.

    args:
        seq_1 (list): list of sequence 1.
        seq_2 (list): list of sequnece 2.

    returns:
        (list) list of lists representing the matrix.
    """

    m = len(seq_1)
    n = len(seq_2)

    # Prepare the initial matrix S.
    Matrix = [[0 for i in range(0, m+1)] for j in range(0, n+1)]

    # Initialization - First row.
    for col in range(1, m+1):
        Matrix[0][col] = col * SCORES["INDEL"]

    # Initialization - First column.
    for row in range(1, n+1):
        Matrix[row][0] = row * SCORES["INDEL"]

    # Compute values for each cell - compute by column.
    # V_1Opcodes: x-axis, V_2Opcodes: y-axis.
    for col in range(1, m+1):
        for row in range(1, n+1):
            match = Matrix[row-1][col-1] + compare_element(seq_1[col-1], seq_2[row-1])
            mismatch = Matrix[row-1][col] + SCORES["INDEL"]
            indel = Matrix[row][col-1] + SCORES["INDEL"]
            Matrix[row][col] = max(match, mismatch, indel)

    return Matrix

def ComputeAlignment(Matrix: list, seq_1: list, seq_2: list):
    """This function computes alignment of two sequence lists based on
    the computed matrix. Note that seq_1 is the default sequence. In other
    words, this function is ocomputing the alignment of seq_1 to seq_2.

    args:
        Matrix (list): list of lists representing the matrix.
        seq_1 (list): list of sequence 1.
        seq_2 (list): list of sequnece 2.

    returns:
        (dict) list of paired elements between seq_1 and seq_2.
    """

    alignedSeqIdxes = {}

    col = len(seq_1)
    row = len(seq_2)
    seq_1Idx = len(seq_1)-1
    seq_2Idx = len(seq_2)-1

    missing = -1

    # Align the two sequences by computing the values in the cell.
    # The pair (seq_1Idx, seq_2Idx).
    while row > 0 and col > 0:
        if (
                (row > 0 and col > 0) and 
                (len(Matrix) > row and len(Matrix[row]) > col) and
                Matrix[row][col] == Matrix[row-1][col-1] + compare_element(seq_1[seq_1Idx], seq_2[seq_2Idx])
        ):
            alignedSeqIdxes[seq_1Idx] = seq_2Idx
            row -= 1
            col -= 1
            seq_1Idx -= 1
            seq_2Idx -= 1
        elif (
                (row > 0 and col > 0) and
                (len(Matrix) > row and len(Matrix[row]) > col) and
                Matrix[row][col] == Matrix[row][col-1] + SCORES["INDEL"]
        ):
            alignedSeqIdxes[seq_1Idx] = missing
            col -= 1
            seq_1Idx -= 1
            missing -= 1
        else:
            alignedSeqIdxes[missing] = seq_2Idx
            row -= 1
            seq_2Idx -= 1
            missing -= 1

    # Make sure that the alignedSeqIdxes to hold all the remaining unmatched element
    # with missing as values, so we know that these unmatched elements are unmatched.
    while seq_1Idx >= 0:
        alignedSeqIdxes[seq_1Idx] = missing
        missing -= 1
        seq_1Idx -= 1

    return alignedSeqIdxes

def compare_element(e1: str, e2: str):
    """This function compares the elements and returns the appropriate score.

    args:
        e1 (str): element from S1.
        e2 (str): element from S2.

    returns:
        (int) either match or mismatch score.
    """

    # DEBUG
    #print (f"e1: {e1}")
    #print (f"   e2: {e2}")

    if e1 == e2:
        return SCORES["MATCH"]
    else:
        return SCORES["MISMATCH"]

def get_elements(nodes: list):
    """This function extracts elements from all nodes in order.

    args:
        nodes (list): list of nodes.

    returns:
        (list) list of elements.
    """

    elements = []

    for node in nodes:
        elements.append(node.element)

    return elements

def reverseAlignedOrder(alignedStrs: dict):
    """This function reverses the aligned string dictionary.

    args:
        alignedStrs (dict): aligned strings.

    returns:
        (dict) reversed align dictionary.
    """

    reversedDict = {}

    i = 0
    j = 0
    for key, val in alignedStrs.items():
        if key > MISSING and val > MISSING:
            reversedDict[i] = j
            i += 1
            j += 1
        elif key > MISSING and val <= MISSING:
            reversedDict[i] = val
            i += 1
        elif key <= MISSING and val > MISSING:
            reversedDict[key] = j
            j += 1

    return reversedDict

def print_matrix(Matrix: list):
    """This function prints the matrix by row.

    args:
        Matrix (list): Matrix, which really is a list of lists.

    returns:
        None.
    """

    for row in Matrix:
        print (row)
