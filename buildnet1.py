import numpy as np
import copy
import random
import time

from warnings import filterwarnings

filterwarnings("ignore", category=RuntimeWarning)

# Genetic Algorithm parameters
POPULATION_SIZE = 100
MUTATION_RATE = 0.3
GENERATIONS = 200
ELITE_SIZE = 0.1
OFFSPRING_UNTOUCHED = 0.05
STUCK_THRESHOLD = 15
LAMARCKIAN_MUTATIONS = 6

# Neural Network parameters
INPUT_SIZE = 16
HIDDEN_SIZE_1 = 32
HIDDEN_SIZE_2 = 16
OUTPUT_SIZE = 1

# Global Variables
best_fitness_list = []


def load_data(filename):
    """
        Data preparation. Load the binary strings data and their corresponding labels from the input text file.
        Returns:
        'data'- numpy 2D array where each row is a binary string from a file line, converted to a list of integers.
        'labels'- numpy 1D array of the labels corresponding to each binary string, converted to integers.
        """
    with open(filename, 'r') as file:
        lines = file.readlines()
    data = []
    labels = []
    for line in lines:
        binary_str, label = line.strip().split()
        data.append([int(bit) for bit in binary_str])  # Convert string to list of ints
        labels.append(int(label))  # Convert label to int

    # data is a 2d array where each row is a list
    return np.array(data), np.array(labels)


def split_train_test(data, labels, test_size=0.2):
    """
        Split data and labels into a train set and a test set.
        the test_size is a fraction of the data to be used as test data.
        Returns x_train (train data), x_test (test data), y_train (train labels), y_test (test labels)
    """
    # Calculate the number of test samples
    num_test_samples = int(len(data) * test_size)
    # Generate random indices for the test set
    test_indices = np.random.choice(len(data), size=num_test_samples, replace=False)
    # Generate train indices as the complement of the test indices
    train_indices = np.setdiff1d(np.arange(len(data)), test_indices)
    # Split the data and labels
    x_train = data[train_indices]
    x_test = data[test_indices]
    y_train = labels[train_indices]
    y_test = labels[test_indices]

    return x_train, x_test, y_train, y_test


# get the data and labels from chosen txt file
data, labels = load_data("nn1.txt")
# Split the data into train and test sets
x_train, x_test, y_train, y_test = split_train_test(data, labels, test_size=0.2)


def create_neural_network():
    """
       creates and initialize a neural network with three layers: two hidden layers and one output layer.
       The sizes of the input layer, hidden layers, and output layer are determined by global variables.
       The output layer includes an activation function.
       """
    model = NeuralNetwork()
    # TODO: add more hidden layers
    model.add_layer(Layer(INPUT_SIZE, HIDDEN_SIZE_1, activation=lambda x: relu(x)))
    model.add_layer(Layer(HIDDEN_SIZE_1, HIDDEN_SIZE_2, activation=lambda x: relu(x)))
    # model.add_layer(Layer(HIDDEN_SIZE_2, HIDDEN_SIZE_3, activation=lambda x: relu(x)))
    # activation layer
    model.add_layer(Layer(HIDDEN_SIZE_2, OUTPUT_SIZE, activation=lambda x: sigmoid(x)))
    return model


def compute_accuracy_score(y_train, predictions):
    """
        Calculates the accuracy score of the predictions made by the network.
        If a prediction matches its true label, it increments the count of correct predictions.
        The accuracy score is the correct predictions divided by the total predictions.
    """
    num_samples = len(y_train)
    correct_predictions = 0

    # If the prediction is correct, increment the count of correct predictions
    for true_label, predicted_label in zip(y_train, predictions):
        if true_label == predicted_label:
            correct_predictions += 1

    # Compute accuracy as the ratio of correct predictions to total number of samples
    accuracy = correct_predictions / num_samples
    return accuracy


def evaluate_fitness(network, x_train, y_train):
    """
        The fitness function evaluates how well the neural network performs on the training data.
        It uses the accuracy of the network's predictions as the fitness score.
    """
    predictions = network.predict(x_train)
    return compute_accuracy_score(y_train, predictions)


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def relu(x):
    return np.maximum(0, x)


def leaky_relu(x):
    return np.maximum(0.1 * x, x)


class GeneticAlgorithm:
    """
        This class represents a genetic algorithm for optimizing the structure and parameters of a neural network.
        The algorithm starts by creating an initial population of random neural networks.
        Then, over a series of generations, it evaluates the performance (fitness) of each network,
        selects the best performers, and breeds a new generation of networks through crossover and mutation.
        At the end of the generations, the algorithm selects the best overall network and returns it.
    """

    def __init__(self):
        self.population_size = POPULATION_SIZE

    # Rank Selection
    def rank_selection(self, population):
        """
        Selects parent networks from the population based on rank-based selection.
        :param population (list): List of neural network objects.
        :return: list: List of selected parent networks for crossover and reproduction.
        """
        # todo: deal with fitness here
        ranked_population = sorted(population, key=lambda network: evaluate_fitness(network, x_train, y_train))
        selection_probs = [rank / len(ranked_population) for rank in range(1, len(ranked_population) + 1)]
        selected_parents = random.choices(ranked_population, weights=selection_probs, k=len(population))
        return selected_parents

    def evolve(self, x_train, y_train):
        # Creating an initial population of neural networks
        population = []
        global best_fitness_list
        for _ in range(self.population_size):
            network = create_neural_network()
            population.append(network)

        best_fitness_so_far = 0
        gen_stuck_count = 0
        for generation in range(GENERATIONS):
            print(f"Generation {generation + 1}/{GENERATIONS}")

            # Evaluating the fitness of each network in the current population
            fitness_scores = []
            for network in population:
                fitness = evaluate_fitness(network, x_train, y_train)
                fitness_scores.append(round(fitness, 5))

            curr_gen_best_fitness = max(fitness_scores)
            print(f"Generation {generation + 1} best fitness score: {curr_gen_best_fitness}")
            best_fitness_list.append(curr_gen_best_fitness)

            # Check if the current generation has achieved maximum fitness
            if curr_gen_best_fitness == 1.0:
                print("successfully converged! reached maximum fitness score of ", curr_gen_best_fitness)
                break
            # Check for early convergence:
            if curr_gen_best_fitness > best_fitness_so_far:
                best_fitness_so_far = curr_gen_best_fitness
                # Reset stuck count if there's improvement
                gen_stuck_count = 0
            else:
                # Increment stuck count if no improvement
                gen_stuck_count += 1

            if gen_stuck_count >= STUCK_THRESHOLD:
                # If no improvement for STUCK_THRESHOLD generations, stop the process
                print("Convergence reached. stuck for ", STUCK_THRESHOLD, " generations")
                break

            # Selecting the top performing networks (elites)
            sorted_indices = np.argsort(fitness_scores)[::-1]
            elite_population = [population[i] for i in sorted_indices[:int(self.population_size * ELITE_SIZE)]]
            # Remaining population after elites have been selected
            remaining_population = list(set(population) - set(elite_population))

            # Creating offspring population via crossover
            offspring_population = []
            num_offsprings = self.population_size - len(elite_population)

            # Rank Selection
            selected_parents = self.rank_selection(remaining_population)

            for _ in range(num_offsprings):
                parent1 = np.random.choice(selected_parents)
                parent2 = np.random.choice(elite_population)
                offspring = parent1.crossover(parent2)
                offspring_population.append(offspring)

            # Save some offspring untouched for the next gen population
            num_untouched_offspring = int(num_offsprings * OFFSPRING_UNTOUCHED)
            untouched_offspring = offspring_population[:num_untouched_offspring]

            # Mutate the remaining (touched) offspring population
            for offspring in offspring_population[num_untouched_offspring:]:
                offspring.mutate()

            # Combine elites, untouched offspring and mutated offspring to create the next gen population
            population = elite_population + untouched_offspring + offspring_population[num_untouched_offspring:]

            # If the genetic algorithm is stuck for more than 3 generations, it triggers the Lamarckian method,
            #  in order to try and get out of a local optima.
            if gen_stuck_count > 3:
                # Lamarckian method:
                print("Lamarckian evolution")
                new_population = []
                # performe Lamarckian evolution on each network in the current population
                for network in population:
                    new_population.append(self.lamarckian_evolution(network, x_train, y_train))
                population = new_population

        # At the end of all the generations/stopped due to convergence/stuck-
        # evaluate the fitness of the last gen population, and select the network with the best fitness        fitness_scores = [evaluate_fitness(network, x_train, y_train) for network in population]
        best_fitness_list.append(max(fitness_scores))
        best_network = population[np.argmax(fitness_scores)]
        return best_network

    # The lamarckian_evolution method tries a specified number of mutations,
    # and accepts the new mutated network only if its fitness is better than the original network
    def lamarckian_evolution(self, network, x_train, y_train):
        old_fitness = evaluate_fitness(network, x_train, y_train)
        # creating a copy of the original network so it will be mutated
        new_network = copy.deepcopy(network)
        for _ in range(LAMARCKIAN_MUTATIONS):
            new_network.mutate()
        # The fitness of the mutated network is now evaluated
        new_fitness = evaluate_fitness(new_network, x_train, y_train)
        # If the mutated network's fitness is better than the original one, we take the mutated network
        if new_fitness > old_fitness:
            return new_network
        else:
            return network


# Layer Class for Neural Network
class Layer:
    """
        This class represents a layer in a neural network model.
        Attributes:
        weights (numpy.ndarray): The weights of the nodes in the layer.
        activation (function): The activation function for the layer.
        The activation function is defaulted to a sigmoid function.
    """

    # Constructs all the necessary attributes for the layer object.
    def __init__(self, input_size, output_size, activation=lambda x: sigmoid(x)):
        # Weights are initialized with Xavier Initialization to optimize training speed
        self.weights = np.random.randn(input_size, output_size) * np.sqrt(1 / input_size)
        # Activation function for the layer
        self.activation = activation

    # Computes the forward propagation of the layer for given inputs
    def forward(self, inputs):
        # Calculate output as matrix product of inputs and weights
        output = np.dot(inputs, self.weights)
        # Apply the activation function to the output
        output = self.activation(output)
        return output

    # Retrieves the shape of the layer's weights and the activation function.
    def get_shape(self):
        return self.weights.shape, self.activation


class NeuralNetwork:
    """
        This class represents a simple feed-forward neural network.
        The network consists of several layers, each represented by a Layer object.
        The network uses these layers to transform its input data when the predict() method is called.
        The class also includes crossover() and mutate() methods.
    """

    def __init__(self):
        # List to hold all layers of the neural network
        self.layers = []

    def add_layer(self, layer):
        # Appends a new layer to the network
        self.layers.append(layer)

    def predict(self, inputs):
        # Passes the inputs through each layer of the network
        outputs = inputs
        for layer in self.layers:
            outputs = layer.forward(outputs)
        # Converts the output of the final layer to binary predictions
        # 0.5 and above no good
        binary_predictions = (outputs > 0.3).astype(int)
        return binary_predictions.flatten()

    def crossover(self, other_network):
        """
            performs a crossover operation between this NeuralNetwork instance and another.
            The crossover combines the weights of the two parents,
            to generate a new offspring network with weights inherited from both parents.
        """
        # # Create the new neural network which will be our offspring
        new_network = create_neural_network()
        for i in range(len(self.layers)):
            alpha = np.random.uniform(0.0, 1.0, size=self.layers[i].weights.shape)
            new_network.layers[i].weights = alpha * self.layers[i].weights + (1 - alpha) * other_network.layers[
                i].weights
        return new_network

    def mutate(self):
        """
        ## TODO: CHANGE THE DOCUMENTATION
        The method is used to randomly adjust the weights in the network's layers to introduce variation.
        the mutation process randomly selects a subset of weights in each layer based on the MUTATION_RATE.
        For the selected weights, a random value (pos/neg) is added to introduce variation.
        """

        # Iterate through each layer in the network
        for layer in self.layers:
            mask = np.random.rand(*layer.weights.shape) < MUTATION_RATE
            # Find the indices where mutation should occur
            mutation_indices = np.where(mask)
            num_mutations = len(mutation_indices[0])

            # If less than 2 mutations, continue to next iteration
            if num_mutations < 2:
                continue

            # Choose two random indices for swapping weights
            random_indices = np.random.choice(num_mutations, size=2, replace=False)
            swap_indices = mutation_indices[0][random_indices]

            # Perform the weight swap to introduce mutation
            temp = layer.weights[swap_indices[0]]
            layer.weights[swap_indices[0]] = layer.weights[swap_indices[1]]
            layer.weights[swap_indices[1]] = temp


start_time = time.time()
# Main
genetic_algorithm = GeneticAlgorithm()
best_network = genetic_algorithm.evolve(x_train, y_train)

# Testing
test_predictions = best_network.predict(x_test)
accuracy = compute_accuracy_score(y_test, test_predictions)
print(f"Test Accuracy: {accuracy}")
end_time = time.time()
runtime = end_time - start_time
minutes = round(runtime / 60)
seconds = runtime % 60
print(best_fitness_list)
print(f"Runtime: {minutes} minutes and {round(seconds, 1)} seconds")