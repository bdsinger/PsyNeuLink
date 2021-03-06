import numpy as np
import psyneulink as pnl

def test_gating():

    Input_Layer = pnl.TransferMechanism(
        name='Input_Layer',
        default_variable=np.zeros((2,)),
        function=pnl.Logistic()
    )

    Output_Layer = pnl.TransferMechanism(
        name='Output_Layer',
        default_variable=[0, 0, 0],
        function=pnl.Linear(),
        output_states={
            pnl.NAME: 'RESULTS USING UDF',
            pnl.FUNCTION: pnl.Linear(slope=pnl.GATING)
        }
    )

    Gating_Mechanism = pnl.GatingMechanism(
        size=[1],
        gating_signals=[Output_Layer.output_state]
    )

    p_pathway = [Input_Layer, Output_Layer]

    stim_list = {
        Input_Layer: [[-1, 30], [-1, 30], [-1, 30], [-1, 30]],
        Gating_Mechanism: [[0.0], [0.5], [1.0], [2.0]]
    }

    comp = pnl.Composition(name="comp")
    comp.add_linear_processing_pathway(p_pathway)
    comp.add_node(Gating_Mechanism)

    comp.run(
        num_trials=4,
        inputs=stim_list
    )

    expected_results = [
        [np.array([0., 0., 0.])],
        [np.array([0.63447071, 0.63447071, 0.63447071])],
        [np.array([1.26894142, 1.26894142, 1.26894142])],
        [np.array([2.53788284, 2.53788284, 2.53788284])]
    ]

    np.testing.assert_allclose(comp.results, expected_results)

def test_gating_using_ModulatoryMechanism():

    Input_Layer = pnl.TransferMechanism(
        name='Input_Layer',
        default_variable=np.zeros((2,)),
        function=pnl.Logistic()
    )

    Output_Layer = pnl.TransferMechanism(
        name='Output_Layer',
        default_variable=[0, 0, 0],
        function=pnl.Linear(),
        output_states={
            pnl.NAME: 'RESULTS USING UDF',
            pnl.FUNCTION: pnl.Linear(slope=pnl.GATING)
        }
    )

    Gating_Mechanism = pnl.ModulatoryMechanism(
        size=[1],
        modulatory_signals=[Output_Layer.output_state]
    )

    p_pathway = [Input_Layer, Output_Layer]

    stim_list = {
        Input_Layer: [[-1, 30], [-1, 30], [-1, 30], [-1, 30]],
        Gating_Mechanism: [[0.0], [0.5], [1.0], [2.0]]
    }

    comp = pnl.Composition(name="comp")
    comp.add_linear_processing_pathway(p_pathway)
    comp.add_node(Gating_Mechanism)

    comp.run(
        num_trials=4,
        inputs=stim_list,
    )

    expected_results = [
        [np.array([0., 0., 0.])],
        [np.array([0.63447071, 0.63447071, 0.63447071])],
        [np.array([1.26894142, 1.26894142, 1.26894142])],
        [np.array([2.53788284, 2.53788284, 2.53788284])]
    ]

    np.testing.assert_allclose(comp.results, expected_results)
